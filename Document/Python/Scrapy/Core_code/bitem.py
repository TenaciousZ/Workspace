#coding:utf8
from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.item import Item, Field
import re
import os
import json
import random
import logging
import sys
from Shop_site_crawler.zsl_spider_lib import fmt_text
reload( sys )
sys.setdefaultencoding('utf-8')



class ProductSpider(Spider):
    '''
    Class doc
    根据商品id抓取天猫平台店铺商品详细信息爬虫
    '''
    name = "bitem"
    download_delay = 1
    start_urls = ['https://detail.tmall.com/item.htm?id=38060962952']  #'https://www.taobao.com']
    custom_settings={
        'ITEM_PIPELINES':{
        # 'Shop_site_crawler.pipelines.pipelines.JsonWithEncodingJdPipeline': 30,#json
        'Shop_site_crawler.pipelines.pipelines.MySQLASync_ItemPipeline': 31,#异步
        }
    }
    max_item_num = 1000 #取店铺商品数量的最大值
    # para  = ''
    # rerun = set()

    def __init__(self, para="62147762:446338500:4502"):
        '''
        Function doc
        这个类的初始化方法
        Parameter doc
        @para : 关键词信息 如:70830413:844169905:41 分别是(店铺id:卖家id:店铺中的宝贝数量)
        '''
        super(ProductSpider, self).__init__()
        if para:
            self.para = para


    def parse(self, response):
        '''
        Function doc
        执行爬虫类scrapy框架默认调用这个方法
        根据关键词,生成url请求网页,获取店铺商品的商品id,并将结果传给下一个回调函数
        Parameter doc
        @response : 请求start_urls 返回的结果集等等... 这里并没用用到
        '''
        if not self.para:
            raise Exception('No have para!')

        if self.para.startswith('items:'):  #方式一:单个商品id为关键词
            for id in self.para[6:].split(','):
                item = ProductItem()
                item['itemid'] = id
                ourl = "http://hws.m.taobao.com/cache/wdetail/5.0/?id=%s&ttid=2013@taobao_h5_1.0.0&exParams={}" % item['itemid']
                yield Request(ourl, meta={'item':item}, cookies={'thw':'cn','hng':'CN_zh-cn_CNY'}, callback=self.parse_item)
        else:   #方式二:多个关键词切割
            for line in self.para.split(','):   #切割关键词字符串
                arr = line.split(':')   #切割每个关键词 如(70830413:844169905:41)
                shopid = arr[0]
                sellerid = arr[1]

                if arr[2] in ['None', '0']:     #没有宝贝的直接退出
                    continue

                if sellerid in ['None', '0']:   #没有卖家id退出
                    continue

                page_num = 12   #每次取店铺的商品数量
                start_num = 0   #取店铺商品的位置 从第0个开始取
                url = 'https://shopsearch.taobao.com/api?inshopn=%d&inshops=%d&userids=%s&callback=jsonp%d&app=api&m=get_shop_auctions' % (page_num, start_num, sellerid, random.randint(100,999))
                yield Request(url, meta={'shopid':shopid,'shopinfo':line,'sellerid':sellerid,'page_num':page_num, 'start_num':start_num}, cookies={'thw':'cn','hng':'CN_zh-cn_CNY'}, callback=self.parse_item_s)


    def parse_item_s(self, response):
        '''
        Function doc
        1.根据商品id抓取详情,回调下一个方法
        2.当店铺商品未抓取完的时候,回调自己
        Parameter doc
        @response : 请求url 返回的结果集等等
        '''
        logging.info("-------"+response.url)
        shopinfo = response.meta['shopinfo']
        shopid = response.meta['shopid']
        sellerid = response.meta['sellerid']
        page_num = response.meta['page_num']
        start_num = response.meta['start_num']
        items = None

        try:
            items = json.loads(response.body[11:-2])
        except:
            logging.info('No JSON object could be decodeds,[shop:%s, %s]' % (shopinfo, response.url))
            return

        for i in items['auctions']: #根据商品id抓取商品详情
            item = ProductItem()
            item['shopid'] = ''
            item['itemid'] = ''
            item['price'] = ''
            item['shop'] = ''
            item['image'] = ''
            item['title'] = ''
            item['amount_30'] = ''
            item['stock'] = ''
            item['favor'] = ''
            item['rate'] = ''
            item['freight'] = ''
            item['shop_promo'] = ''
            item['guarantee'] = ''
            item['props'] = ''
            item['skualias'] = ''
            item['shop_start'] = ''
            item['skuprops'] = ''
            item['promo'] = ''
            item['ori_price'] = ''
            item['mprice'] = ''
            item['cat_id'] = ''
            item['brand'] = ''
            
            item['shopid']     = shopid
            item['itemid']     = i['nid']
            item['price']      = i['price']
            ourl = "http://hws.m.taobao.com/cache/wdetail/5.0/?id=%s&ttid=2013@taobao_h5_1.0.0&exParams={}" % item['itemid']
            yield Request(ourl, meta={'item':item}, cookies={'thw':'cn','hng':'CN_zh-cn_CNY'}, callback=self.parse_item)

        if ( len(items['auctions']) == 12 
                and start_num < self.max_item_num ):    #抓取店铺中所有商品
            start_num += 12
            logging.info('shop item start num:'+ str(start_num))
            url = 'https://shopsearch.taobao.com/api?inshopn=%d&inshops=%d&userids=%s&callback=jsonp%d&app=api&m=get_shop_auctions' % (page_num, start_num, sellerid, random.randint(100,999))
            yield Request(url, meta={'shopid':shopid,'shopinfo':shopinfo,'sellerid':sellerid,'page_num':page_num, 'start_num':start_num}, cookies={'thw':'cn','hng':'CN_zh-cn_CNY'}, callback=self.parse_item_s)
        
    def parse_item(self, response):
        '''
        Function doc
        解析response.body,将结果返回管道类(pipelines)
        Parameter doc
        @response : 请求url 返回的结果集等等
        yield dict(字典)
        '''
        logging.info("----------"+response.url)
        item = response.meta['item']
        data  = json.loads(response.body)
        data  = data['data']
        value = []

        try:
            value = json.loads(data['apiStack'][0]['value'])
        except:
            info = 'No JSON object could be decoded [%s, %s]' % (item['shopid'], response.url)
            if response.body.decode('utf-8').find(u'\u4e0d\u5b58\u5728') != -1:
                logging.info(info)
            else:
                # self.rerun.add(item['itemid'])
                logging.info(info)
            return

        if 'shopid' not in item or not item['shopid']:  #店铺id
            item['shopid'] = data['seller']['shopId']

        item['shop'] = data['seller']['shopTitle']  #店铺名称
        item['image'] = data['itemInfoModel']['picsPath'][0] if 'picsPath' in data['itemInfoModel'] else ''     #商品大图片
        item['title'] = fmt_text(data['itemInfoModel']['title'])    #标题
        vinfo = value['data']['itemInfoModel']
        # amount_30 月销量
        item['amount_30'] = vinfo['totalSoldQuantity'] if 'totalSoldQuantity' in vinfo else ''  
        item['stock'] = vinfo['quantity']   # stock库存
        item['favor'] = data['itemInfoModel']['favcount']   # favor收藏
        item['rate'] = data['rateInfo']['rateCounts']   # rate
        item['freight'] = value['data']['subInfos'][0]      # freight  快递费用
        item['shop_promo'] = ''# shop_promo
        
        for f in value['data']['subInfos']:
            if f.startswith(u'\u5feb\u9012') or f.startswith(u'\u8fd0\u8d39'):
                item['freight'] = f
                break

        if 'shopPromotion' in value['data']:
            sp = value['data']['shopPromotion']
            if 'title' in sp and 'descriptions' in sp:
                item['shop_promo'] = sp['title'] + ':' + ';'.join(sp['descriptions'])

        guarantee = []  # guarantee
        if 'layoutData' in value['data'] and 'GUARANTEES' in value['data']['layoutData']['replaceDataMap']:
            guarantee = value['data']['layoutData']['replaceDataMap']['GUARANTEES'].strip('[]').split(',')
        elif 'guaranteeInfo' in value['data'] and 'afterGuarantees' in value['data']['guaranteeInfo']:
            guarantee = [i['title'] for i in value['data']['guaranteeInfo']['afterGuarantees']]
        
        item['guarantee'] = ';'.join([x.strip('"') for x in guarantee])     #卖家保证
        item['props'] = ''  

        if 'props' in data: # props 商品详情
            item['props'] = ';'.join(x['name'] + ':' + x['value'] for x in data['props'])

        item['skualias'] = ''
        skualias = []

        if 'skuProps' in data['skuModel']:
            skus = data['skuModel']['skuProps']
            for sku in skus:
                propId = sku['propId']
                for v in sku['values']:
                    skualias.append(propId + ':' + v['valueId'] + '@' + v['name'].replace(',', ' '))

        item['skualias'] = '^'.join(skualias) # skualias  尺码,颜色,大小,
        # shop_start #开店时间
        item['shop_start'] = data['seller']['starts'] if 'starts' in data['seller'] else ''
        item['skuprops'] = ''
        
        skuprops = {}
        if 'skus' in value['data']['skuModel']: 
            skus = value['data']['skuModel']['skus']
            for k in skus.keys():
                disprice = skus[k]['priceUnits'][0]['price']
                price    = skus[k]['priceUnits'][1]['price'] if len(skus[k]['priceUnits']) > 1 else disprice
                stock    = skus[k]['quantity']
                skuprops[k] = {'skuid':k, 'disprice':disprice, 'price':price, 'stock':stock}

        asku = []
        for (k,v) in skuprops.items(): 
            asku.append('%s@%s;%s;%s' % (v['skuid'], v['price'], v['disprice'], v['stock']))
        item['skuprops'] = '^'.join(asku)   # skuprops skuid@原价,现价,库存^
        priceUnits = value['data']['itemInfoModel']['priceUnits']
        
        item['promo'] = ''
        if 'tips' in priceUnits[0]:     # promo #活动
            if 'txt' in priceUnits[0]['tips'][0]:
                item['promo'] = priceUnits[0]['tips'][0]['txt']
            elif len(priceUnits[0]['tips']) > 1 and 'txt' in priceUnits[0]['tips'][1]:
                item['promo'] = priceUnits[0]['tips'][1]['txt']

        # for 11.11
        if item['promo'].find(u'\u53cc11') != -1:
            item['promo'] = '11.11'

        # for 12.12
        if item['promo'].find(u'12\u9884\u552e') != -1:
            item['promo'] = '12.12'

        # ori_price原价
        if len(priceUnits)>1:
            item['ori_price'] = priceUnits[1]['price'] if 'price' in priceUnits[1] else ''
        if 'ori_price' not in item or not item['ori_price']:
            item['ori_price'] = priceUnits[0]['rangePrice'] if 'rangePrice' in priceUnits[0] else priceUnits[0]['price']

        # price 现价
        if 'price' not in item or not item['price']:
            item['price'] = priceUnits[0]['price']

        # mprice 现价
        item['mprice'] = priceUnits[0]['price']
        if 'tips' in priceUnits[0]:
            for i in priceUnits[0]['tips']:
                if 'txt' in i and i['txt'].find(u'\u624b\u673a\u4e13\u4eab') != -1:
                    item['mprice'] = priceUnits[0]['price']

        item['cat_id'] = data['trackParams']['categoryId']#类目id
        item['brand'] = '' 

        if 'props' in data:  # brand 品牌
            for i in data['props']:
                if u'\u54c1\u724c' in i['name']:
                    item['brand'] = i['value']
                    break

        yield self.wipe_comma(item)


    def wipe_comma(self, item):
        '''
        Function doc
        替换字典value值中的','(逗号)并去除首尾的引号
        Parameter doc
        @item : 字典(dict)
        return dict(字典)
        '''
        for k in item.keys():
            if isinstance(item[k], (str,unicode)):
                item[k] = item[k].replace(',', ' ').strip().strip('"').strip("'")
        return item


    # end ProductSpider



class ProductItem(Item):
    '''
    Class doc
    字段列表
    '''
    shop       = Field()
    shopid     = Field()
    itemid     = Field()
    title      = Field()
    image      = Field()
    amount_30  = Field()
    amount_all = Field()
    ori_price  = Field()
    price      = Field()
    mprice     = Field()
    stock      = Field()
    favor      = Field()
    rate       = Field()
    cat_id     = Field()
    props      = Field()
    skuprops   = Field()
    freight    = Field()
    is_new     = Field()
    guarantee  = Field()
    shop_start = Field()
    shop_promo = Field()
    skualias   = Field()
    brand      = Field()
    promo      = Field()
    prepay     = Field()
    coupon     = Field()
    combo      = Field()
    dt         = Field()
    updated    = Field()
    plat       = Field()
