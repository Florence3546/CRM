#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import csv
import time
import signal
from multiprocessing import Pool, Queue

from django.core.management.base import BaseCommand, CommandError

from apps.router.models import User
from apps.subway.models import Keyword, Adgroup
from apps.subway.models_adgroup import DoesNotExist
from apps.common.utils.utils_log import log
from apps.kwlib.select_base import ItemScorer
from apps.kwlib.analyzer import ChSegement

POOLSIZE = 8
queue = Queue()


class SimpleCSV(object):
    rows = []

    def __init__(self, columns):
        self.rows.append(columns.split())

    def add_row(self, args):
        self.rows.append(args)

    def add_rows(self, rows):
        for row in rows:
            self.add_row(row)

    def save(self, filename):
        with open(filename, 'wb') as f:
            writer = csv.writer(f)
            writer.writerows(self.rows)


def load_atoms(cat_id):
    log.info('Loading atom words in category: {:<10}'.format(cat_id))
    atoms = []
    for atom in ChSegement._get_collection().find({}, {'word': 1}):
        atoms.append(atom['word'])
    log.info('%d atom words loaded.' % len(atoms))
    return atoms


def get_item(keyword):
    try:
        adgroup = Adgroup.objects.get(adgroup_id = keyword['adgroup_id'])
    except DoesNotExist:
        return None
    return adgroup.item


def get_psd(item):
    ps = item.product_word_list
    ss = item.sale_word_list
    ds = item.get_decorate_word_list()
    return ps, ss, ds


def get_scorer(keyword):
    # item = get_item(keyword)
    return ItemScorer()


def item_url(shop_id, item_id):
    shop_type = User.objects.get(shop_id = shop_id).shop_type
    domain = 'detail.tmall.com' if shop_type == 'B' else 'item.taobao.com'
    return 'http://{domain}/item.htm?id={item_id}'.format(**locals())


def count_deals(keyword):
    deals = 0
    for report in keyword['rpt_list']:
        direct = int(report['directpaycount'])
        indrect = int(report['indirectpaycount'])
        deals += direct + indrect
    return deals


def find_keywords(atom):
    keywords = Keyword._get_collection().find({
        'word': {'$regex': atom},
        '$or': [
            {'rpt_list.directpaycount': {'$gt': 0}},
            {'rpt_list.indirectpaycount': {'$gt': 0}}]})
    log.info('Found %d keywords' % keywords.count())
    return keywords


def scan(atoms):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    keyword_total = 0
    logged_keyword = 0
    for i, atom in enumerate(atoms):
        log.info('Finding keywords contain %s[%d/%d]...' % (atom, i, len(atoms)))
        for keyword in find_keywords(atom):
            keyword_total += 1
            item = get_item(keyword)
            if not item:
                continue
            ps, ss, ds = get_psd(item)
            label_words = ps + ss + ds
            word = keyword['word'].replace(' ', '')
            scorer = get_scorer(keyword)
            left = scorer.extract_labels(word)[-1]
            score, labels = scorer.score_participles_by_item(word)
            url = item_url(keyword['shop_id'], item.item_id)
            deals = count_deals(keyword)
            if atom not in label_words: # if score < 1000:
                logged_keyword += 1
                queue.put((
                    atom,
                    keyword['word'],
                    ''.join(labels),
                    ','.join(ps),
                    ','.join(ss),
                    ','.join(ds),
                    left,
                    url,
                    deals))
                log.info('Processing %d/%d keywords' % (logged_keyword, keyword_total))
    queue.put('DONE')


def iter_atoms(atoms):
    length = len(atoms)
    log.info('Atom count: %d' % length)
    piece_size = length / POOLSIZE
    for i in range(POOLSIZE):
        st = i * piece_size
        ed = st + piece_size
        if i == POOLSIZE - 1 or ed > length:
            ed = length
        log.info('Slicing atoms[%d:%d]' % (st, ed))
        yield atoms[st:ed]


class Command(BaseCommand):
    filename = 'user_synonyms_%d.csv' % time.time()
    args = '[output-file (default: %s)]' % filename
    help = '收集用户认定的同义词'

    def handle(self, *args, **options):
        filename = args[0] if len(args) > 0 else self.filename
        if os.path.exists(filename):
            raise CommandError('Output file exists!')
        pool = Pool(POOLSIZE)
        pool.map_async(scan, iter_atoms(load_atoms(16)))
        finished_worker = 0
        result = SimpleCSV(u'原子词 关键词 标签 P S D 未匹配部分 宝贝URL 成交数')
        try:
            while finished_worker < POOLSIZE:
                row = queue.get()
                if row == 'DONE':
                    finished_worker += 1
                    log.info('Worker[%d] finished!' % finished_worker)
                else:
                    result.add_row(row)
                    log.info('Adding row: %d' % len(result.rows))
        except KeyboardInterrupt:
            log.warn('KeyboardInterrupt received, terminating...')
        finally:
            pool.terminate()
            result.save(filename)
            log.info('Finished: %s' % filename)
