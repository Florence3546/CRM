# coding=UTF-8

import init_environ
from apps.kwlib.select_base import MemcacheAdpter

cat_ids = '50020275 50009979'
cat_id_list = cat_ids.split()


result_list = []
for cat_id in cat_id_list:
    word_list = MemcacheAdpter.get_large_list(cat_id, 'kwlib')
    print 'cat word count:', cat_id, len(word_list)
    if word_list:
        for kw in word_list:
            if u'山药' in kw[0]:
                result_list.append([cat_id, kw[0]])

print 'result_list:', len(result_list)

for rl in result_list[:50]:
    print rl[0], rl[1]
