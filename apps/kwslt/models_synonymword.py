# coding=UTF-8
from apps.kwslt.models_cat import Cat
from apps.common.cachekey import CacheKey
from mongoengine.document import Document
from mongoengine.fields import IntField, StringField
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_log import log

class SynonymWord(Document):
    '''
    .同义词词库.类目名称以一级类目为组织
    '''
    cat_id = IntField(verbose_name = "类目ID")
    cat_name = StringField(verbose_name = "类目名", max_length = 100)
    word_list = StringField(verbose_name = "同义词词串", max_length = 1024)
    meta = {"collection":"kwlib_synonymword", "db_alias": "kwlib-db"}

    @staticmethod
    def reload_single_cat_synoword(cat_id):
        flag_dict = CacheAdpter.get(CacheKey.KWLIB_SYNOWORD % -1, 'web', {'init':''})
        if not flag_dict.has_key('init'):
            objs = SynonymWord.objects.filter(cat_id = cat_id)
            word_dict = {}
            if objs:
                for obj in objs:
                    word_list = obj.word_list.split(',')
                    temp_dict = { word.replace('\r', ''):word_list for word in word_list }
                    word_dict.update(temp_dict)
                CacheAdpter.set(CacheKey.KWLIB_SYNOWORD % cat_id, word_dict, 'web', 60 * 60 * 24 * 7)
            else:
                CacheAdpter.delete(CacheKey.KWLIB_SYNOWORD % cat_id, 'web')
            log.info('update synoword into memcache, cat_id=%s' % cat_id)
        else:
            SynonymWord.load_in_cache_if_not()

    # 加载到内存中
    @staticmethod
    def load_in_cache_if_not():
        flag_dict = CacheAdpter.get(CacheKey.KWLIB_SYNOWORD % -1, 'web', {'init':''})
        if not flag_dict.has_key('init'):
            return

        temp_cat_id = -1
        word_dict = {}
        syno_word_list = SynonymWord.objects.all().order_by('cat_id')
        for sw in syno_word_list:
            if not sw:
                continue
            word_list = sw.word_list.split(',')
            temp_word_dict = { word.replace('\r', ''):word_list for word in word_list }
            if sw.cat_id == temp_cat_id:
                word_dict.update(temp_word_dict)
            else:
                CacheAdpter.set(CacheKey.KWLIB_SYNOWORD % temp_cat_id, word_dict, 'web', 60 * 60 * 24 * 7)
                temp_cat_id = sw.cat_id
                word_dict = temp_word_dict
        CacheAdpter.set(CacheKey.KWLIB_SYNOWORD % temp_cat_id, word_dict, 'web', 60 * 60 * 24 * 7)
        log.info('init all synoword into memcache')

    # 根据一系列的词，选中同义词
    # TODO:直接根据词到同义词词库中匹配，会遗漏掉一些词，比如 女鞋，就找不到对应的词，实际上，女士鞋、女用些,都可以，需要分解匹配
    @staticmethod
    def get_synonym_words(cat_id, word_list):
        SynonymWord.load_in_cache_if_not()
        result_list = []
        cat_id_list = Cat.get_cat_attr_func(cat_id, "cat_path_id").split(' ') + [0]
        syno_dict = {}
        for cat_id in cat_id_list:
            temp_dict = CacheAdpter.get(CacheKey.KWLIB_SYNOWORD % cat_id, 'web', {})
            for word, syno_word_list in temp_dict.items():
                if syno_dict.has_key(word):
                    syno_dict[word].extend(syno_word_list)
                else:
                    syno_dict[word] = syno_word_list
        for wl in word_list:
            result_list.extend(syno_dict.get(wl, []))
        return result_list

synoword_coll = SynonymWord._get_collection()
