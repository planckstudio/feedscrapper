import requests
import json
import time
import os
from decouple import config
from feedgen.feed import FeedGenerator
import urllib.parse
import base64
import wget

class Instagram(object):
    def __init__(self):
        print("init")

    def create_dir(self,path):
        isExist = os.path.exists(path)
        if not isExist:
            os.makedirs(path)

    def get_as_base64(self,url):
        return base64.b64encode(requests.get(url).content)

    def save_img(self,url, name):
        path = "./tmp/img/" + name + ".jpg"
        isExist = os.path.exists(path)

        if isExist:
            print("img exists")
        else:
            self.create_dir("./tmp/img/")
            wget.download(url, out=path)
    
    def get_user(self,username):
        payload = {}

        url = "https://i.instagram.com/api/v1/users/web_profile_info/?username=" + username
        headers = {
            "Cookie": config('IGSESSION'),
            "X-IG-App-ID": config('IGAPPID'),
            "User-Agent": config('IGUSERAGENT'),
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.text)


    def gen_user_media_rss(self,username, total, next=""):
        user = self.get_user(username)
        data = json.loads(self.get_user_media(user["data"]["user"]["id"],total,next))
        
        fg = FeedGenerator()
        fg.id(user["data"]["user"]["id"])
        fg.title("Posts by " + username + " On Instagram")
        fg.author( {'name':user["data"]["user"]["full_name"]} )
        fg.description(user["data"]["user"]["biography"])
        fg.generator("Feed")
        fg.link( href='https://feed.planckstudio.in/instagram/user/' + username, rel='alternate' )
        fg.logo(user["data"]["user"]["profile_pic_url"])
        fg.subtitle(user["data"]["user"]["category_name"])
        fg.link( href='https://www.instagram.com/' + username, rel='self' )
        fg.language('en')

        try:
            for edges in data["data"]["user"]["edge_owner_to_timeline_media"]["edges"]:
                ext = ".jpg"
                url = edges["node"]["display_url"]
                li = "https://www.instagram.com/p/" + str(edges["node"]["shortcode"])
                fe = fg.add_entry()
                fe.id(li)
                fg.author( {'name':user["data"]["user"]["full_name"]} )
                fe.title("@"+username)
                fe.link(href=li)
                imgurl = config('HOST') + "img/" + str(edges["node"]["shortcode"])
                self.save_img(url, edges["node"]["shortcode"])
                img = '<div><img src="'+imgurl+'" width="1080px" height="1080px" alt="" /></div>'
                try:
                    fe.content(type='encoded',content='<![CDATA[ '+ img +'')
                    fe.description(edges["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"])
                except IndexError:
                    print("No caption")
        except json.decoder.JSONDecodeError:
            print("Error")
        
        return fg


    def get_user_media(self,id, total, next=""):
        links = ""
        url = (
            "https://www.instagram.com/graphql/query/?query_hash=003056d32c2554def87228bc3fd9668a&variables=%7B%22id%22%3A%22"
            + str(id)
            + "%22%2C%22first%22%3A"
            + str(total)
            + "%2C%22after%22%3A%22"
            + next.replace("=", "%3D")
            + "%22%7D"
        )

        payload = {}

        headers = {
            "Cookie": config('IGSESSION'),
            "X-IG-App-ID": config('IGAPPID'),
            "User-Agent": config('IGUSERAGENT'),
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        return response.text
