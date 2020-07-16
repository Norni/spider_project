import json
import os
from qianqianyinyue.utils.mongo_pool import MongoPool
# from qianqianyinyue.utils.log import logger
from qianqianyinyue.core.spiders.artist_total import ArtistTotal
from qianqianyinyue.core.spiders.author_info_update import AuthorInfoUpdate
from qianqianyinyue.core.spiders.song_total import SongTotal
from qianqianyinyue.core.spiders.song_info_total_update import SongInfoTotalUpdate


class ProcessConsole():
    def __init__(self):
        self.mongo_pool_ = MongoPool(collection="artist")
        self.mongo_pool = MongoPool(collection="songs")

    def _save_info_to_file(self, conditions):
        song_info = self.mongo_pool.find_one(conditions)
        if song_info:
            with open('song_list.txt', 'w+', encoding='utf8') as f:
                for song in song_info["song_list"]:
                    f.write(json.dumps(song, ensure_ascii=False, indent=2))
                    f.write(os.linesep)
                    f.write('*'*20)
                    f.write(os.linesep)
            return "写入文件完成"
        return "写入文件出错：未找到该数据"

    def _check_artist_data(self):
        artist = self.mongo_pool_.find_all()
        if not artist:
            ArtistTotal().run()
            AuthorInfoUpdate().run()
            return "数据加载完成,欢迎使用"
        return "数据加载完成,欢迎使用"

    def _check_author_by_author_name(self, author_name):
        conditions = {"author_name": author_name}
        artist = self.mongo_pool_.find_one(conditions)
        if artist:
            conditions = {"author_info.author_name": author_name}
            if self.mongo_pool.find_one(conditions):
                print("找到了该歌手数据，正在更新数据,请稍后查收文件song_list.txt")
                SongInfoTotalUpdate().run(author_name)
                self._save_info_to_file(conditions)
            else:
                print("找到了该歌手数据，正在下载数据,请稍后查收文件song_list.txt")
                SongTotal().run(author_name)
                SongInfoTotalUpdate().run(author_name)
                self._save_info_to_file(conditions)
        else:
            print("数据库中，无法找到该歌手，请核对无误后再输入")

    def run(self):
        print("欢迎使用歌曲查找系统，该系统能通过歌手名字，查找该歌手的所有歌曲信息")
        print("数据加载中...请稍等...")
        message = self._check_artist_data()
        print(message)
        author_name = input("请输入要查找的歌手名字：")
        self._check_author_by_author_name(author_name)


if __name__ == "__main__":
    ProcessConsole().run()