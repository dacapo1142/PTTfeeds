#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from collections import namedtuple, deque
from urllib.parse import urlparse, urlunparse
from lxml import html
from html2text import html2text
import requests


class PttBoardParser:
    '''The PTT board parser, which can fetch new posts from a single board.'''
    MAX_SCAN_COUNT = 10000
    ANCHORS_COUNT = 3
    POSTS_SCOPE_XPATH = './/*[@class="r-list-container action-bar-margin bbs-screen"]/*'
    NEXT_PAGE_XPATH = '//*[@id="action-bar-container"]/div/div[2]/a[2]/@href'

    class Record(namedtuple('Record', 'id_set, post_queue')):
        '''The data structure that store anchor posts'''
        pass

    class Post:
        '''The data structure that store a single post.'''
        class PostParsingError(Exception):
            '''Exception'''
            pass

        TITLE_XPATH = './div[@class="title"]/a/text()'
        DATE_XPATH = './div[@class="meta"]/div[@class="date"]/text()'
        AUTHOR_XPATH = './div[@class="meta"]/div[@class="author"]/text()'
        PARTIAL_URL_XPATH = './div[@class="title"]/a/@href'

        def __init__(self, html_post):
            try:
                self.title = html_post.xpath(self.TITLE_XPATH)[0]
                self.date = html_post.xpath(self.DATE_XPATH)[0]
                self.author = html_post.xpath(self.AUTHOR_XPATH)[0]
                partial_url = html_post.xpath(self.PARTIAL_URL_XPATH)[0]
                url = urlunparse(
                    urlparse(html_post.base_url)._replace(path=partial_url))
                self.url = url
                self.post_id = self.url_to_id(url)
                req = requests.get(url)
                self.content = html2text(req.text).replace('\n\n', '\n')
            except:
                raise self.PostParsingError(
                    'The selected post has been deleted.')

        def __eq__(self, other):
            return self.post_id == other.post_id

        def __hash__(self):
            return self.post_id.__hash__()

        def __str__(self):
            return '{}, {}\n{}\n{}'.format(
                self.date, self.author, self.title, self.url)

        def __repr__(self):
            return self.title

        def url_to_id(self, link):
            '''convert post id (a.k.a AID) to url'''
            return link.split('/')[-1].replace('.html', '')

    def __init__(self, board_name, rules):
        url = 'https://www.ptt.cc/bbs/{}/index.html'.format(board_name)
        self.board_name = board_name
        self.url = url
        self.gen_anchors(self.ANCHORS_COUNT)
        self.rules = rules

    def gen_posts(self, number, url=None):
        '''return new posts'''
        first_page = False
        if not url:
            first_page = True
            url = self.url

        req = requests.get(url)
        web = html.fromstring(req.text, base_url='https://www.ptt.cc')
        html_posts = web.xpath(PttBoardParser.POSTS_SCOPE_XPATH)
        if not html_posts:
            raise Exception('PttBoardParserError',
                            'The structure of PTT web has been changed')

        if first_page:
            from itertools import takewhile
            # the following function exclude sticky posts from candidate posts
            html_posts = takewhile(
                lambda x: x.attrib['class'] != 'r-list-sep', html_posts)

        html_posts = reversed(list(html_posts))
        for html_post in html_posts:
            # parsing order : from bottom to top
            if number > 0:
                try:
                    post = self.Post(html_post)
                    # print(post)
                    if hasattr(self, 'record') and (post.post_id in self.record.id_set):
                        break
                    number = number - 1
                    yield post
                except self.Post.PostParsingError:
                    # skip the deleted post
                    pass
            else:
                break
        else:
            nexturl = web.xpath(PttBoardParser.NEXT_PAGE_XPATH)[0]
            url = urlunparse(urlparse(url)._replace(path=nexturl))
            yield from self.gen_posts(number, url)

    def gen_anchors(self, anchors_count):
        '''generate anchor posts from a board'''
        posts = list(self.gen_posts(anchors_count))
        id_set = {aid.post_id for aid in posts}
        post_queue = deque(posts)
        self.record = self.Record(id_set, post_queue)

    def renew_anchors(self, posts):
        '''renew anchor posts from a board'''
        self.record.post_queue.extendleft(reversed(posts))
        self.record.id_set.update({post.post_id for post in posts})
        while len(self.record) > self.ANCHORS_COUNT:
            post = self.record.post_queue.pop()
            self.record.id_set.remove(post.post_id)

    def scan_new_posts(self):
        '''scan and rewnew anchar posts'''
        posts = list(self.gen_posts(self.MAX_SCAN_COUNT))
        self.renew_anchors(posts)
        return posts

    def check_rules(self, post):
        '''return the corresponding subscribers if meeting a rule'''
        for rule in self.rules:
            if 'author' in rule and rule['author'] != post.author:
                continue
            if 'title' in rule and not any(map(lambda x: x in post.title, rule['title'])):
                continue
            if 'content' in rule and not any(map(lambda x: x in post.content, rule['content'])):
                continue
            yield from rule['subscribers']

    def subscribed_posts(self):
        posts = self.scan_new_posts()
        selected_posts = [(post, list(self.check_rules(post)))
                          for post in posts]
        selected_posts = filter(
            lambda x: True if x[1] else False, selected_posts)
        return list(selected_posts)


if __name__ == '__main__':

    import json
    try:
        with open('settings.json') as f:
            settings = json.load(f)
    except:
        settings = dict()
        settings['gmail_user_id'] = input('Please enter gmail user id: ')
        settings['boards'] = dict()
        while True:
            board_name = input('enter the name of the board: ')
            rules=list()
            while True:
                rule=dict()
                while True:
                    subscribers = input('enter the subscribers (seperate with space, cannot be empty): ').split()
                    if subscribers:
                        break
                rule['subscribers']=subscribers
                author = input('enter author name (default:none): ')
                title = input('enter the key words in title (default:none, seperate with space): ').split()
                content = input('enter the key words in content (default:none, seperate with space): ').split()
                
                if author:
                    rule['author']=author
                if title:
                    rule['title']=title
                if content:
                    rule['content']=content
                rules.append(rule)
                if input('enter more rules? (Y/n): ').strip().lower() == 'n':
                    break
            settings['boards'][board_name]=rules
            if input('enter more boards? (Y/n): ').strip().lower() == 'n':
                break
        
        with open('settings.json','w') as f:
            import jsbeautifier
            print(jsbeautifier.beautify(json.dumps(settings)), file=f)

                
            

    import yagmail
    yag = yagmail.SMTP(settings['gmail_user_id'])
    yag.close()

    def parser_constructor_wrapper(board):
        board_name = board['name']
        board_rules = board['rules']
        return PttBoardParser(board_name, board_rules)

    board_parsers = []
    from concurrent.futures import ThreadPoolExecutor
    from termcolor import colored
    with ThreadPoolExecutor(max_workers=3) as executor:
        for board_parser in executor.map(lambda x: PttBoardParser(*x), settings['boards'].items()):
            print('The initialization of parsing board::{} has been completed.'.format(
                colored(board_parser.board_name, 'blue')))
            board_parsers.append(board_parser)

    def sendmail(subject, body, subscribers):
        '''send email to corresponding subscribers'''
        yag = yagmail.SMTP(settings['gmail_user_id'])
        for subscriber in subscribers:
            yag.send(to=subscriber, subject=subject, contents=body)
        yag.close()

    while True:
        import time
        with ThreadPoolExecutor(max_workers=3) as excutor:
            for selected_posts in excutor.map(lambda x: x.subscribed_posts(), board_parsers):
                for post, subscribers in selected_posts:
                    subject = post.title
                    url_html = '<a href="{0}">{0}</a>\n\n'.format(post.url)
                    body = url_html + post.content
                    sendmail(subject, body, subscribers)
                    print('send {} to the following subscribers: {}'.format(
                        colored(subject, 'green'),
                        colored(','.join(subscribers), 'green')))
        time.sleep(60)
