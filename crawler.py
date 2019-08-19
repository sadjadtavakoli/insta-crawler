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
    # posts = []
    for username in username_list:
        # if username != username_list[0]:
        #     sleep(random.randint(100, 200))
        try:
            response = requests.get(base_url.format(username))
            content = json.loads(response.content)
            info = content['graphql']['user']['edge_owner_to_timeline_media']
            post_count = info['count']
            print("=====getting-----{}-{}----".format(base_url.format(username), post_count))
            end_cursor = info['page_info']['end_cursor']
            next_page = info['page_info']['has_next_page']
            print("has next next_page  {}".format(next_page))

            shortcodes = []
            # username_posts = []
            for item in info['edges']:
                shortcodes.append(item['node']['shortcode'])
            print(shortcodes)
            store_id, is_enough = get_users_posts(shortcodes)
            print(is_enough)
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
    rdb.connect('localhost', 28015).repl()

    username_list = ["zibana_poshak", "zarinbaft2017", "zara_oysho", "yaam_shopping", "wlcom_shop",
                     "viva_bootik", "vans_iran_", "vania_gallery", "uniqueaniya",
                     "uniq_butik_yazd", "turk_onlinesales", "touranj_gallery", "touka.design",
                     "tootfarangi_moeinmall", "tip1_bags_shoes", "tinaashoes", "tiktak.sport",
                     "the_queen_mezon", "tandor.gallery", "taksport_ramin", "tabriiiz.leather",
                     "street_style_btq", "stop__fashion", "star.shopss", "sport_collection_shoes",
                     "soma_collection", "sohani_shoes", "skirt_city", "shose_org", "shopping_alma",
                     "shomiz_majlesii", "shoes_online90", "shoegallery_papion", "shinkhatoon",
                     "shine_mezon_gharb", "shiko.shoes", "shicoshoes", "shakibli", "shafei_shoes",
                     "shaani.official", "sh.zangeneh20", "seyedshoping", "saturnstore.online",
                     "sarisa_shoes", "sarcci_", "sandal_home", "samshik_sport", "samaa_charm",
                     "saeedsportshoes", "sadafgallery1", "sabagallery.1", "russell.collection",
                     "run_sport.foad", "rosha_atlas", "ros.mod", "romans_gallery",
                     "roma_collectionn", "rangtarang", "prana__gallery",
                     "poshakbamboo", "poshak_style_", "pooshakth", "pooshak.shana",
                     "pooshak_ela98", "pik__shop", "peony.designgallery", "parsilashoopp",
                     "parii_collection", "pardis_storee", "paradox.bandarabbas",
                     "paradox_dark_shop", "panik26933", "painted_handmades_47", "paeizan_official",
                     "padoosh_leather", "outletcenter_j", "orginal_arman",
                     "ordibehesht.book.store", "online_mahdisa_shop", "nike_sport_org",
                     "nike_regal", "negin.gallery.bojnurd", "negar.illustration.88",
                     "nazpooshgallery", "narvan.clothes", "mr__katooni", "mp_boutik",
                     "mod_pooshann", "mod_pooshann", "mkhsports", "mimnon.handmades", "mielshaa",
                     "mezune.farzaneh", "mezonevenice", "mezone_maahak", "mezon.sonia.ahwaz",
                     "mezon_shikkk6", "mezon_sepidi", "mezon_sararoohi1",
                     "mezon_mahpari_kifokafsh", "meshkat.gallery", "mercata.ir", "mb.bagesfahan",
                     "matrishandicrafts", "markshopt", "manto_domi", "manesa_shop", "mandy_jame",
                     "maison.company", "mahoot.collection", "mahgogalery", "madam.gallery",
                     "maaangallery", "luxury_mezon_online_", "lusso_e_bella", "lusiferkaraj",
                     "lunodiia", "loveengallery", "leyshe.leather", "lebas_majlessi",
                     "leather.v.m", "leather.mari", "leather_zip", "lavisan1396",
                     "lavin_pleated_skirt", "lando_bad_shoes", "laleeneh", "kok.talaii",
                     "kochila.shop", "kifokafsh_taj_panik", "kifkafshe.bela", "kifkafsh_setareh",
                     "kifado", "kif_ahora", "kia_moda", "kayagallery", "katuni_yang",
                     "katooni_original62", "katooni_mn", "katooni_kafsh", "katonidragon",
                     "katonidavod", "katoni_shikpa", "katoni_orgin", "katoni_brandstyle",
                     "karhaye_manodastam", "kalasion", "kafsherisk", "kafshbest", "kafsh.zananeh",
                     "kafsh_kamelia", "kafsh_as_", "jical_skirt", "jest_capri", "janan_brnd",
                     "ivazshop", "iran.dress2", "inja_off", "ibolak", "hutch_gallery",
                     "humehr_leather", "honaredast_leather", "heroo3909", "healer_sport",
                     "harmony_leather_", "handmade.nargesss", "hajamooo", "girly_swankystyle",
                     "girls_store.ir", "gilas_crafts", "gifter_shop", "ghasedak.bag",
                     "gallerydianaa", "gallery_nariman", "gallery_diiiiba", "flamingo_handmades",
                     "fashion__gallery1", "fara.online.shopping", "elma.leather", "elimoonmezon",
                     "eli.va.baroon", "dvandishoes", "dogo_turk", "demitbag", "delphos.clothing",
                     "davidgones_fatemi", "dastaan_gallery", "darkoob.dress", "daman_plisse_satin",
                     "daman_pelise", "d_minali", "cinar_shoes", "chooblebasi5", "checkitonline",
                     "charmshideh_ahwaz", "charmgan", "charmak_leather", "charm_lili__",
                     "cele_mode", "carpisa_iran", "cactus.boutiquee", "butikmilla__",
                     "boutique_yaas", "botiqe_avijeh", "botiqe_avijeh", "boticlamisrasht",
                     "bornila.gallery", "bolourian.fashionshop", "bndruning", "best_mezoon",
                     "behell.ir", "batis.butique", "barton_shoes", "barana_19_97",
                     "bahar_leather97", "azaliya_shoes", "atefe.naderi.design", "as_boutiquee2",
                     "arnikaa_gallery", "armana_shop", "aris.onlineshop", "ariat.gallery",
                     "ador_charm", "3sisters_mezon", "_uniquecollection_", "_sol_leather",
                     "_saarang_", "_ariamode_", "__shikopick__", "__moderuz__",
                     "zimo.design",
                     "zhinojewelry",
                     "Zhevan cosmetics",
                     "zh.o.o.r",
                     "zarsima.ara",
                     "zarinbaft2017",
                     "zarifi.clothing",
                     "zanbagh.jewelry",
                     "woodartplus",
                     "witty_scarf",
                     "wishmodaa",
                     "vianagallery",
                     "valeh_design",
                     "tukhe.gallery",
                     "tokangolbahar",
                     "tinam_gallery",
                     "thuluthjewelry",
                     "tarahi_lebas_morabba",
                     "tanpooshmahdokht",
                     "tandor.gallery",
                     "tajkhatoon_scarf",
                     "sylque_by_sadaf",
                     "store_avaa",
                     "stop__fashion",
                     "star.shopss",
                     "sportavaran",
                     "soraya.gallery",
                     "Soonesh",
                     "sooart.ir",
                     "soheil.gallery",
                     "sodreh.art",
                     "sky_scarf",
                     "sigma.bag",
                     "shyngallery",
                     "shidecollection",
                     "shenilsha",
                     "sheemenchitsaz",
                     "shanti_handicraft",
                     "shamdooonia",
                     "shalitedesign",
                     "shafei_shoes",
                     "set.men",
                     "sepanta.giftbox",
                     "secretscarf1989",
                     "secheke_handmade",
                     "sayna.scarf",
                     "sasondesign",
                     "sarina.store",
                     "samen.design",
                     "samanehleather",
                     "sadhandmade",
                     "sadepoosh",
                     "sacci_gallery",
                     "royal_womens",
                     "roselite_iran",
                     "riramezon1",
                     "remode021",
                     "rees_collection",
                     "Ravis_scarf",
                     "ranginkaman.balloon",
                     "rama.mens",
                     "rainbo_land",
                     "raad___design",
                     "queen_mezon",
                     "pusak_babak",
                     "prime._.leather",
                     "prima.online.shopping",
                     "prag_jewelry",
                     "pooshema",
                     "pooshake_dook",
                     "pooshak_ela98",
                     "pino__shop",
                     "peony_gallery",
                     "patiram_socks",
                     "parsagoliran",
                     "Paris.shoesandbag.qeshmisland",
                     "pardis_storee",
                     "paisley_scarf",
                     "paeez.galleria",
                     "novellashawlls",
                     "noraa.online",
                     "niloo_jewelry",
                     "nikoo_mezon",
                     "nasimkh.jewelry",
                     "nareng_crafts",
                     "naargoon",
                     "mulberry.scarf",
                     "morvvvarid_",
                     "moon__gallery2",
                     "montra_jewelry",
                     "monjogh_gallery",
                     "modart_gallery",
                     "misssmart_ir",
                     "miss.moriss",
                     "miriyamjewelry",
                     "mezun_baaraan",
                     "mezonshek",
                     "mezoneunique",
                     "mezoneorkid",
                     "Mezon_ronika_scarf",
                     "mezon_mester",
                     "mezon_dark_violet",
                     "mezon.janse",
                     "merlovv",
                     "mehregan_gold_gallery",
                     "medichiladieslounge",
                     "matrishandicrafts",
                     "matoskahhippiestyle",
                     "masoo_gallery",
                     "masha_gallery",
                     "marta_bags",
                     "maroo_design",
                     "Marmarin_gallery",
                     "mantosevda91",
                     "manto_venisa",
                     "manto_sonati_tanposh_ariyaee",
                     "manto_pegah",
                     "manto_pargol",
                     "manto_lalond",
                     "manto_atoosa_axon",
                     "mandy_jame",
                     "mandanamani",
                     "mahtaab.design",
                     "mahootab",
                     "Mahoor_art20",
                     "mahatmamezon",
                     "macho.scarf",
                     "maaangallery",
                     "lux._box",
                     "liro_handmade",
                     "lilia_gallery",
                     "liilii_style",
                     "leyshe.leather",
                     "level.women",
                     "Lebas__design",
                     "leather.mari",
                     "lara_namad",
                     "koleehandworks",
                     "kolah_farang",
                     "kolah.shal.iran",
                     "kif.novin.mehdi",
                     "khatoon.javaher",
                     "khallvat",
                     "kerchief.1",
                     "karimihandicrafts",
                     "kahroba_gallery2015",
                     "janan_brnd",
                     "janamond",
                     "iranzaminmezon",
                     "indianshop98",
                     "hutch_gallery",
                     "humehr_leather",
                     "hoodo.mens",
                     "hiva__mezon",
                     "Hiedra_rosa",
                     "hi_mod_",
                     "hedocheshm",
                     "havva_wear",
                     "harir.official",
                     "haniran_design",
                     "handmade_matilda",
                     "hana_mezone",
                     "haina_design",
                     "goolaviz_handmade",
                     "goldoonche",
                     "golbox_",
                     "giftland1",
                     "ghasedak.bag",
                     "gandomhandmade",
                     "gandom_accessoriess",
                     "gallery_kaaf_2017",
                     "fazzi_art",
                     "farvardinqom",
                     "eynakgovanji",
                     "esterella.ir",
                     "elysee_cosmetics",
                     "elswan_socks",
                     "elma.leather",
                     "eli.va.baroon",
                     "DookStore",
                     "dogmeh",
                     "delfi.gift",
                     "davin_mezon",
                     "davidjones_princess",
                     "davidjones_ir",
                     "dark_man_mezon",
                     "chehraknarimani",
                     "chatrephiroozeh",
                     "charmani.leather",
                     "charm_lan",
                     "chapar_shoes",
                     "chameh_gallery",
                     "cham_couture",
                     "ch__gallery",
                     "celio_woman",
                     "bobo____shop",
                     "bluewaterdiamond",
                     "bigol_art",
                     "beh.accessories",
                     "batisgallery.ring",
                     "azurestudio",
                     "avina_onlineshop",
                     "avidaccessories",
                     "ava_gallerry",
                     "atrin_minakari",
                     "atre.bahaar",
                     "as_scarf1",
                     "as_boutiquee2",
                     "artmis.toubagallery",
                     "aroosmarket",
                     "annasani",
                     "annamiss_jewelry",
                     "amish.official",
                     "8Clocks",
                     "_sana_bano_94",
                     "_.sevdameson._",

                     ]
    get_users_info(username_list)
