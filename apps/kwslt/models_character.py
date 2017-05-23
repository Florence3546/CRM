# coding=UTF-8
from mongoengine import Document
from mongoengine.fields import StringField


class Character(Document):
    word = StringField(verbose_name = "汉字", max_length = 10, required = True, unique = True)

    meta = {"collection":"kwlib_word", "db_alias": "kwlib-db"}

    @classmethod
    def get_all_character(cls):
        return [wd['word'] for wd in character_coll.find()]

character_coll = Character._get_collection()
