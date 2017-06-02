import scrapy


class MLSpider(scrapy.Spider):
    name = 'ml_spider'
    # allowed_domains = ['mercadolibre.com.uy']
    start_urls = ['']
    # user_ml = 'dalepo@hotmail.com'
    user_ml = 'd378722@mvrht.net'

    # step 1 - ir a http://www.mercadolibre.com.uy/
    def parse(self, response):
        url_login = response.css('#nav-header-menu > a.option-login::attr(href)').extract_first()
        return scrapy.Request(url=url_login, callback=self.parse_login)

    # step 2 - Login 1 (username)
    def parse_login(self, response):
        url_post = response.css('#login_user_form::attr(action)').extract_first()
        return [scrapy.FormRequest(response.urljoin(url_post),
                                   formdata={'user_id': self.user_ml, 'kstrs': ''},
                                   callback=self.parse_login2)]

    # step 3 - Login 2 (pass + tokens)
    def parse_login2(self, response):
        url_post = response.css('#login_user_form::attr(action)').extract_first()
        return [scrapy.FormRequest(url=url_post,
                                   formdata={
                                       'user_id': self.user_ml,
                                       'password': 'potter1',
                                       'dps': response.css('#dps::attr(value)').extract_first(),
                                       'callback_error': response.css('#callback_error::attr(value)').extract_first(),
                                       'platform_id': 'ML',
                                       'site_id': 'MLU'
                                   },
                                   callback=self.parse_home)]

    # step 4 - Redirect a busqueda
    def parse_home(self, response):
        return scrapy.Request(url=':P',
                              callback=self.parse_listings)

    # step - 5 parse info
    def parse_listings(self, response):
        self.log('Starting spider...')
        items = response.css('div.rowItem')
        for item in items:
            info = {
                'nombre': item.css('h2.list-view-item-title a::text').extract_first(),
                'precio': item.css('ul.details li.costs span::text').extract_first(),
            }
            # obtener detalle del item
            url_detalle = item.css('h2.list-view-item-title a::attr(href)').extract_first()
            yield scrapy.Request(
                response.urljoin(url_detalle),
                meta={'info': info},
                dont_filter=True,
                callback=self.parse_details
            )
        # se sigue paginacion
        next_page_url = response.css('li.last-child > a::attr(href)').extract_first()
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    def parse_details(self, response):
        str_na = "N/A"
        info = response.meta.get('info', {})
        reputations = response.css('div.reputation-info dd > strong::text').extract()
        if len(reputations) == 4:
            info['vendedor'] = {
                'tipo': 'Vendedor Premium',
                'recomendaciones': reputations[0],
                'ventas': reputations[1],
                'rank': reputations[2],
                'antiguedad': reputations[3]
            }
        else:
            info['vendedor'] = {
                'tipo': 'Vendedor Comun',
                'recomendaciones': str_na,
                'ventas': str_na,
                'rank': str_na,
                'antiguedad': str_na
            }
        yield info
