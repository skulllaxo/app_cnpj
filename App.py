import scrapy
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from scrapy.http import TextResponse
from datetime import datetime
from time import sleep
import pandas as pd
import numpy as np
import os


class App():
    name = 'App'
    allowed_domains = ['appasp.sefaz.go.gov.br']
    start_urls = ['http://appasp.sefaz.go.gov.br/Sintegra/Consulta/default.asp']

    def __init__(self):
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.driver.get(self.start_urls[0])
        

    
    def consult_cnpj(self,cnpj):
        self.cnpj = cnpj
        #get consult window
        consult_page = self.driver.window_handles[0]

        self.driver.switch_to_window(consult_page)
        self.driver.refresh()

        #Selecting CNPJ document option 
        cnpj_button = self.driver.find_element_by_id('rTipoDocCNPJ')
        cnpj_button.click()

        #Adding CNPJ in field
        cnpj_field = self.driver.find_element_by_id('tCNPJ').send_keys(self.cnpj)


        #Consult document
        submit_button = self.driver.find_element_by_css_selector('div.controls > input[type=submit]') 
        submit_button.click()

    def get_form_data(self):

        #convert date dd/mm/YYYY to YYYY/mm/dd
        def convert_date(date_field:dict) -> dict :
            
            field_name = list(date_field.keys())[0] 

            date = date_field[field_name]

            if date != 'NULL':

                converted_date = datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")
            else:
                converted_date = date

            return {field_name:converted_date}

        #Find key and value in selectors
        def find_field(selectors,key:str) -> dict:
            key = key.lower()
            value_list = []
            key_found = False

            for n_sel,selector in enumerate(selectors):

                #if text_selector is None, replace value to NULL
                try:
                    text_selector = selector.css('::text').get().lower().replace('\n','').replace('\t','')
                except AttributeError:
                    text_selector = 'NULL'

                if len(text_selector) ==0:
                    print(text_selector)

                class_selector = selector.css('::attr(class)').get()

                if class_selector == 'label_title':

                    if key in text_selector:

                        key_found = True
                        key_name = text_selector.replace(':','')
                        
                    else:
                        key_found = False

                
                if key_found and class_selector == 'label_text':
                    value_list.append(text_selector)
                    
            try:
                value_list = list(set(value_list))
                value = ' | '.join(value_list)
                field = {key_name:value}
            except NameError:
                field = {key:'NULL'}
            
            return field


        #Swith to form page
        form_page = self.driver.window_handles[1]
        self.driver.switch_to_window(form_page)


        html_page = self.driver.page_source
        response = TextResponse(url = '',body = html_page, encoding = 'utf8') 
        
        #Get all tables in html
        tables = response.css('tbody').css('td span')

        cnpj = {'cnpj':self.cnpj}
        inscricao_estadual = find_field(tables,'Inscrição Estadual') 
        nome_empresarial = find_field(tables,'Nome empresarial') 
        contribuinte = find_field(tables,'Contribuinte') 
        atividade_principal = find_field(tables,'ATIVIDADE ECONÔMICA')
        situacao_cadastral_vigente = find_field(tables,'Situação Cadastral Vigente')
        
        data_situacao_cadastral = find_field(tables,'Data desta situação cadastral')
        data_situacao_cadastral = convert_date(data_situacao_cadastral)
        
        data_cadastramento = find_field(tables,'Data de cadastramento') 
        data_cadastramento = convert_date(data_cadastramento)

        self.driver.switch_to_window(form_page)
        self.driver.close()
        return {'cnpj':cnpj,
               'inscricao_estadual':inscricao_estadual,
               'nome_empresarial':nome_empresarial,
               'contribuinte':contribuinte,
               'atividade_principal':atividade_principal,
               'situacao_cadastral_vigente':situacao_cadastral_vigente,
               'data_situacao_cadastral':data_situacao_cadastral,
               'data_cadastramento':data_cadastramento
               }


def main():
    HOME = os.getenv('HOME')

    df = pd.read_csv('f{HOME}/app_cnpj/cnpj.csv')
    app = App()

    rows = []
    for cnpj in df['cnpj'].values:
        
        cnpj = str(cnpj)
        app.consult_cnpj(cnpj)
        sleep(2)

        row = {}
        data = app.get_form_data()
        sleep(2)
        #add values in row dict
        [row.update(field) for field in data.values()]
        
        #add row in rows
        rows.append(row)
        
    df = pd.DataFrame(rows)
    df = df.replace(np.nan, 'NULL', regex=True)

    df.to_csv('sefaz_go.csv')       

if __name__ == '__main__':
    main()
    


    