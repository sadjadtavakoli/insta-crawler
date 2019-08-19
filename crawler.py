# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import json
import random
from time import sleep

import requests
import rethinkdb as r


def usage():
    return """
        python crawler.py -t boolean 
        for true value, crawl all data, for false value crawl just today.
    """


base_url = " https://instagram.com/{}/?__a=1"
next_page_url = "https://www.instagram.com/graphql/query/?query_hash=f2405b23" \
                "6d85e8296cf30347c9f08c2a&variables="
next_page_url_variables = {'id': {},
                           'first': 25,
                           'after': {}}
post_base_url = "https://www.instagram.com/p/{}/?__a=1"
post_pure_url = "https://www.instagram.com/p/{}/"


def get_user_post(shortcode):
    sleep(1)
    post_url = post_base_url.format(shortcode)
    print("----get user's post----")
    response = {}

    try:
        response = requests.get(post_url)
        content = json.loads(response.content)['graphql']['shortcode_media']
        images = []
        post_json = {}

        images_list = content.get("edge_sidecar_to_children", None)
        if images_list:
            image_edges = images_list['edges']
            for edge in image_edges:
                image = edge['node']['display_url']
                images.append(image)
        else:
            image = content['display_url']
            images.append(image)

        post_json['image_urls'] = images
        post_json['caption'] = content['edge_media_to_caption']['edges'][0]['node']['text']
        insta_date = datetime.datetime.fromtimestamp(
            content['taken_at_timestamp'])
        post_json['instagram_date'] = str(insta_date)
        post_json['post_url'] = post_pure_url.format(shortcode)
        post_json['store_id'] = content['owner']['id']
        post_json['store_name'] = content['owner']['username']
        post_json['read'] = False
        return post_json, insta_date < datetime.datetime.now() - datetime.timedelta(
            days=4)

    except:
        f = open('log.txt', "w+", encoding="utf-8")
        f.write(response.content)
        f.write(shortcode)
        f.write("×××××××××××××××××××××")
        f.close()
        return None, False


def get_users_posts(shortcodes):
    is_enough = False
    last_item = None
    store_id = None
    cursor = rdb.table("insta_crawler")
    for item in shortcodes:
        post_json, is_enough = get_user_post(item)

        if not last_item:

            store_id = post_json['store_id']
            last_posts = cursor.order_by('instagram_date').filter({'store_id': store_id}).run()
            if last_posts:
                last_item = last_posts[-1]

        if last_item and last_item['post_url'] == post_json['post_url']:
            is_enough = True

        else:
            save(post_json)

        if is_enough:
            break
    return store_id, is_enough


def get_users_info(username_list):
    for username in username_list:
        try:
            response = requests.get(base_url.format(username))
            content = json.loads(response.content)
            info = content['graphql']['user']['edge_owner_to_timeline_media']
            post_count = info['count']
            print("=====getting-----{}-{}----".format(base_url.format(username), post_count))
            end_cursor = info['page_info']['end_cursor']
            next_page = info['page_info']['has_next_page']
            print("has next next_page: {}".format(next_page))

            shortcodes = []
            for item in info['edges']:
                shortcodes.append(item['node']['shortcode'])
            print(shortcodes)
            store_id, is_enough = get_users_posts(shortcodes)
            print("is enough? ", is_enough)
            while not is_enough and next_page:
                print("has next next_page  {}".format(next_page))
                shortcodes, end_cursor, next_page = get_basics_info(store_id,
                                                                    end_cursor)
                print(shortcodes)
                store_id, is_enough = get_users_posts(shortcodes)
        except:
            print("page is private! or BLOCK!!")


def get_basics_info(store_id, end_cursor):
    next_page_url_variables['id'] = store_id
    next_page_url_variables['after'] = end_cursor
    response = requests.get(next_page_url + json.dumps(next_page_url_variables))
    content = json.loads(response.content)
    info = content['data']['user']['edge_owner_to_timeline_media']
    end_cursor = info['page_info']['end_cursor']
    next_page = info['page_info']['has_next_page']
    shortcodes = []
    for item in info['edges']:
        shortcodes.append(item['node']['shortcode'])
    return shortcodes, end_cursor, next_page


def save(data):
    rdb.table("insta_crawler").insert(data).run()


if __name__ == "__main__":
    rdb = r.RethinkDB()
#   connecting to reThinkDb, for data writing. if u are using another ways for wrinting data, this part is unnecessary. 
    rdb.connect('localhost', 28015).repl()

    username_list = []
    get_users_info(username_list)
