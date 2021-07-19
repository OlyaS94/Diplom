#!/usr/bin/env python
# coding: utf-8

# In[4]:


import requests, pprint, urllib, json, datetime
from datetime import datetime
from urllib.parse import urljoin
from pprint import pprint


class Photo:
    name = ''

    def __init__(self, date, likes, sizes):
        self.date = date
        self.likes = likes
        self.sizes = sizes
        self.size_type = sizes['type']
        self.url = sizes['url']
        self.maxsize = max(sizes['width'], sizes['height'])

    def __repr__(self):
        return f'date: {self.date}, likes: {self.likes}, size: {self.maxsize}, url: {self.url}'


class VK:
    base_url = "https://api.vk.com/method/"

    @staticmethod
    def find_largest(sizes):
        sizes_list = ['x', 'z', 'y', 'r', 'q', 'p', 'o', 'x', 'm', 's']
        for types in sizes_list:
            for size in sizes:
                if size['type'] == types:
                    return size

    def __init__(self):
        self.token = 'b206235d00f59a404c70fc755d9bd9206a866d9fef80626768f5010d2c57af9fbd2258a25cd37deaea853'
        self.version = '5.131'

    def get_photos(self, user, quantity=5):
        get_url = urljoin(self.base_url, 'photos.get')
        resp = requests.get(get_url, params={
            'access_token': self.token,
            'v': self.version,
            'owner_id': user,
            'album_id': 'profile',
            'photo_sizes': 1,
            'extended': 1
        }).json().get('response').get('items')

        return sorted([Photo(photo.get('date'),
                             photo.get('likes')['count'],
                             self.find_largest(photo.get('sizes'))) for photo in resp],
                      key=lambda p: p.maxsize, reverse=True)[:quantity]


class Yandex:

    @staticmethod
    def file_names(photos):
        for photo in photos:
            photo.name = str(photo.likes)
            if [p.likes for p in photos].count(photo.likes) > 1:
                photo.name += '_' + str(photo.date)
            photo.name += '.jpg'

    @staticmethod
    def folder_name(n_folder, ex_folders):
        if n_folder not in ex_folders:
            return n_folder
        n = 1
        n_folder += '_' + str(n)
        while n_folder in ex_folders:
            n_folder = n_folder.replace('_' + str(n), '_' + str(n + 1))
            n += 1
        return n_folder

    def __init__(self, token: str):
        self.auth = f'OAuth {token}'

    def get_folders(self):
        return [p['name'] for p in (requests.get("https://cloud-api.yandex.net/v1/disk/resources",
                                                 params={"path": '/'},
                                                 headers={"Authorization": self.auth})
                                    .json().get('_embedded').get('items')) if p['type'] == 'dir']


    def create_folder(self, folder_name):
        resp = requests.put("https://cloud-api.yandex.net/v1/disk/resources",
                            params={"path": '/' + folder_name},
                            headers={"Authorization": self.auth})
        print(f'Creating folder "{folder_name}":' + str(resp.status_code))
        return resp.ok



    def upload(self, user, photos):
        upload_folder = self.folder_name(user, self.get_folders())
        self.file_names(photos)
        if self.create_folder(upload_folder):
            log_result = []
            for photo in photos:
                response = requests.post("https://cloud-api.yandex.net/v1/disk/resources/upload",
                                         params={"path": '/' + upload_folder + '/' + photo.name,
                                                 "url": photo.url},
                                         headers={"Authorization": self.auth})
                if response.status_code == 202:
                    print(f'Фото "{photo.name}" загружено на диск.')
                    log_result.append({"file_name": photo.name, "size": photo.size_type})
                else:
                    print(f'Ошибка загрузки "{photo.name}": '
                          f'{response.json().get("message")}. Status code: {response.status_code}')
            with open(f'{user}_{datetime.now().strftime("%m_%d_%Y_%H_%M_%S")}_files.json', "w") as f:
                json.dump(log_result, f, ensure_ascii=False, indent=2)


def init():
    ya_token = input('Яндекс токен:')
    user = input('Вконтакте id:')
    quantity = input('Количество: ')
    vk_user= VK()
    ya_api: Yandex = Yandex(ya_token)
    ya_api.upload(user, vk_user.get_photos(user, int(quantity)))


if __name__ == '__main__':
    init()


# In[ ]:




