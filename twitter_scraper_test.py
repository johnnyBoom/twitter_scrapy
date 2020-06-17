#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time:  2020-5-31 0:05
# @Author: 张海达
# @File: twitter_scraper_test.py
# @Software: PyCharm

from twitter_scraper import get_tweets

import time
import hmac
import hashlib
import urllib.parse

import requests
import json

import re
# from googletrans import Translator
# 导入mysql驱动
import mysql.connector
import base64


def getDingTailSign():
    timestamp = str(round(time.time() * 1000))
    secret = 'SECa9b568a8e6bc9ecbc13ca01d673ea764c02788df40208fb01b2941aa483f315d'
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    signDic = dict(timestamp=timestamp, sign=sign)
    return signDic


def postMessage(userName, pages):
    # conn = mysql.connector.connect(user="root", password="root123", host="localhost", database="test", buffered=True)
    conn = mysql.connector.connect(user="root", password="root123", host="localhost", database="twitter_scrap",
                                   buffered=True)
    cursor = conn.cursor()
    try:
        for tweet in get_tweets(userName, pages=pages):
            # print(tweet)
            tweetId = tweet["tweetId"]
            username = tweet["username"]
            tweetUrl = tweet["tweetUrl"]
            isRetweet = tweet["isRetweet"]

            # 抓取到的数据每一条进行判断，按ID查找，在数据库里存在不操作，不存在发送请求给机器人，然后保存
            select_query = "SELECT count(1) FROM twitter_scraper WHERE tweetId  = " + tweetId + ";"
            try:
                cursor.execute(select_query)
                c = cursor.fetchone()[0]
            except mysql.connector.Error as err:
                c = 0
            if c == 0:
                # print("发送机器人请求")
                text1 = tweet["text"]
                p = "pic\.twitter\.com.*"
                text = re.sub(p, "", text1)
                entries = tweet["entries"]
                title = ""
                if isRetweet:
                    title = userName + "转发了" + username + "的推特"
                else:
                    title = userName + "更新了推特"
                photoList = entries["photos"]
                joinPhotoList = []
                if len(photoList):
                    # 对图片列表中的每个图片进行本地保存，文件名是twitterID+第几张
                    photoListNew = []
                    for i in range(len(photoList)):
                        data = requests.get(photoList[i])
                        filename = tweetId + "-" + str(i) + ".png"
                        with open(filename, 'wb') as fp:
                            fp.write(data.content)
                        photoListNew.append("http://45.32.75.149:8080/" +filename)
                    def joinPhoto(x):
                        return "![image](" + x + ")"
                    joinPhotoList = list(map(joinPhoto, photoListNew))

                markDownList = ["#### " + title + "\n\n", text + "\n\n", joinPhotoList,
                                "[原文链接](https://twitter.com" + tweetUrl + ")"]
                markdownText = ""
                for c in markDownList:
                    if type(c).__name__ == 'list':
                        for v in c:
                            markdownText = markdownText + v + "\n\n"
                    else:
                        markdownText = markdownText + c + "\n\n"
                # print(markdownText)
                dingTalkSing = getDingTailSign()
                boturl = "https://oapi.dingtalk.com/robot/send?" \
                         "access_token=5da1a623d549026fba616a3358e8557725af32f6ca681671b2930b0790b44bb0" \
                         "&timestamp=" + dingTalkSing['timestamp'] + \
                         "&sign=" + dingTalkSing['sign']
                headers = {'Content-Type': 'application/json;charset=utf-8'}

                data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": title,
                        "text": markdownText
                    }
                }
                r = requests.post(boturl, data=json.dumps(data), headers=headers)

                if "ok" in r.text:
                    # 发送机器人请求成功后，插入到数据库
                    insert_query = 'INSERT INTO twitter_scraper  (tweetId, username, tweetUrl, isRetweet ,text)'
                    insert_query += ' VALUES ( %s, %s, %s, %s, %s)'
                    try:
                        cursor.execute(insert_query, (
                            tweetId,
                            username,
                            tweetUrl,
                            isRetweet,
                            text
                        ))
                    except mysql.connector.Error as err:
                        print(err.msg)
                    else:
                        # print(cursor.rowcount)
                        conn.commit()
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


def main():
    # userList = ["realDonaldTrump", "elonmusk"]
    userList = ["elonmusk"]
    for user in userList:
        postMessage(user, 1)


if __name__ == '__main__':
    main()
