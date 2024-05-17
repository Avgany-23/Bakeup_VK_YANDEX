import requests
import json


class VK:
    url_basic = "https://api.vk.com/method/"

    def __init__(self, token, user_id, version="5.131"):
        self.__token = token
        self.__id = user_id
        self.__version = version
        self.params = {"access_token": self.__token, "v": self.__version}

    def get_url(self, method):  # Для URL адреса
        return self.url_basic + method

    def __str__(self):
        """Краткая информация о пользователе"""
        url = self.url_basic + "users.get"
        user = requests.get(url, params={**self.params, "user_ids": self.__id}).json()["response"][0]
        return (f'Имя: {user['first_name']}\nФамилия: {user['last_name']}\n'
                f"id профиля: {user['id']}\nТип профиля: {'Закрытый' if user['is_closed'] else 'Открытый'}")

    def get_photos_profile(self, size=1, album=0):  # Получение фоток со страницы ВК и их название
        """
        :param size: 1 - по умолчанию макс. размер, size -1 - минимальный размер
        :param album: 0 - по умолчанию возвращаются фотографии с профиля, 1 - со стены
        :return: ссылка, кол-во лайков и название (из ссылки) фотографии. Сортировка фоток по возрастанию лайков
        """
        if not isinstance(size, int) or size not in (-1, 1):  # Проверка на корректность параметра size
            raise TypeError("параметр size целое число, равное 1 или -1")
        if not isinstance(album, int) or album not in (0, 1):  # Проверка на корректность параметра album
            raise TypeError("параметр album целое число, равное 0 или 1")

        albums = {0: "profile", 1: "wall"}

        url = self.get_url("photos.get")
        params = {**self.params, "owner_id": self.__id, "album_id": albums[album], "extended": 1}
        response = requests.get(url, params=params).json()['response']['items']

        url_photo = [i["sizes"][-1 * size]["url"] for i in response]  # Ссылка на фотографию
        likes_photo = [l["likes"]["count"] for l in response]  # Количество лайков у фотографии
        photo_name = [u[u.find("/") + 2: u.find(".")] for u in url_photo]  # Имя фотографии (из ссылки)

        return list(zip(url_photo, likes_photo, photo_name))

    def save_photo_yandex(self, token, folder='VK_photo', size=1, album=0):
        """
        Загрузка фотографий из профиля ВК на Яндекс диск
        :param token: ключ Яндекс диска (обязательный параметр)
        :param folder: указывает папку куда загрузить фото. Если такой нет, то автоматически создаться.
        По умолчанию название папки - VK_photo
        :return: возвращает содержимое json файла
        """
        info = self.get_photos_profile(size, album)
        albums = {0: "profile", 1: "wall"}

        if not info:
            print("Фотографии не нашлись, загружать нечего")
            return -1

        self.create_folder_yandex(token, folder=folder)

        size_ = "m" if size == -1 else "z"
        json_info = []

        for url, like, name in info:  # Загрузка фото
            url_ = "https://cloud-api.yandex.net/v1/disk/resources/upload"
            headers = {'Authorization': token}
            params = {'path': f"{folder}/лайки - {like}, имя - {name}"}
            response = requests.get(url_, headers=headers, params=params)

            try:
                requests.put(response.json()['href'], files={'file': requests.get(url).content})
            except KeyError:
                print(f"Фотография {name} из каталога '{albums[album]}' уже загружена в папку {folder}")
            else:
                print(f"Фотография {name} успешно загружена в папку {folder}")
                json_info.append({"file_name": f"{like}.jpg", "size": size_})

        print('Загрузка завершена')

        with open(f"{folder}.json", "w", encoding="utf-8") as f:  # Загрузка в json файл характеристик фотографий
            json.dump(json_info, f, indent=2)

        return json_info

    def create_folder_yandex(self, token, folder='VK_photo'):  # Создание папки на яндекс диске
        '''
        :param token: токен пользователя
        :param folder: обязательный параметр, название папки
        '''
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = {'Authorization': token}
        params = {'path': folder}
        response = requests.put(url, headers=headers, params=params)
        if response.status_code == 409:
            print(f"Папка {folder} уже создана, загрузка фотографий производится в неё")
        else:
            print(f"На диске создана папка {folder}")


vk_token = ''  # Указывается токен к ВК
yandex_token = ''  # Указывается токен к Яндекс Диску
user_id = ''  # Указывается ID страницы, с которой будут скачиваться фотографии

vk_user = VK(vk_token, user_id)
vk_user.save_photo_yandex(token=yandex_token, folder='photo_VK', size=1, album=0)