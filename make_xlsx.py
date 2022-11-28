import xlsxwriter, csv, os, parser
from time import sleep
from progress.bar import IncrementalBar

def try_except(input_func):    
    def output_func(*args):
        try:
            input_func(*args)
        except Exception as e:
            with open('errors.txt', 'a') as file:
                file.write(f'\n\n--------------Exception:--------------\n{e}')
    return output_func 

@try_except
def make_xlsx(path_input:str='input_table.csv', path_output:str = 'out_table.xlsx', full_table:bool = False):
    if not os.path.exists(path_input):
        print('Вхідного файла не існує. По стандарту він має мати назву "input_table.csv". Або уведіть свою назву та шлях дофайлу, за допомогою тегу -pi')
        with open('errors.txt', 'a') as error_file:
            error_file.write(f'\n\nВхідного файла не існує. Path:{path_input}')
        return
    
    with open('input_table.csv', 'r') as file_in:
        row_count = sum(1 for line in file_in)
    
    with open(path_input, 'r') as file_in:
        print('Вхідний файл відкрито.')
        reader = csv.reader(file_in, delimiter=';')
        
        if os.path.exists(path_output):
            os.remove(path_output)
            print('Стару вихідну таблицю видалено.')
        
        output_table = xlsxwriter.Workbook(path_output)
        xlsx_list = output_table.add_worksheet('output_list')
        
        bold = output_table.add_format({'bold': True})
        italic = output_table.add_format({'italic': True})
        usd = parser.get_usd()
        linecount = 1
        
        xlsx_list.set_column(0,0,35)
        xlsx_list.set_column(1,1,20)
        xlsx_list.set_column(2,2,6)
        xlsx_list.set_column(3,3,6)
        xlsx_list.set_column(4,4,3)
        xlsx_list.set_column(5,5,40)
        
        xlsx_list.write(0, 0, 'Назва товару', bold)
        xlsx_list.write(0, 1, 'Варіант', bold)
        xlsx_list.write(0, 2, 'ref Ціна', bold)
        xlsx_list.write(0, 3, 'makeup Ціна', bold)
        xlsx_list.write(0, 4, 'Склад', bold)
        xlsx_list.write(0, 5, 'URL', bold)
        
        finish_print = ''
        print('Початок створення таблиці. Це може зайняти декілька хвилин...')
        progresbar = IncrementalBar('Прогрес', max = row_count)
        for i in reader:
            sleep(3)
            progresbar.next()
            product = parser.parse_makeup(i[0])
            product_new = {'check':False, 'positions':[]}
            try:
                if i[2] != '': ref_prise  = round(float(i[2].replace(',','.'))*usd)
                elif i[3] != '': ref_prise = int(i[3])
                else:
                    finish_print += f'\nПозицію {product["name"]} ({product["url"]}) пропущено, так як немає жодного значення ref price'
                    continue
            except:
                finish_print += f'\nПозицію {product["name"]} ({product["url"]}) пропущено, тому що значення ref price некоректне'
                continue
            
            for variant in product['positions']:  
                if (ref_prise < variant['price'] or ((i[1] != '') and i[1] not in variant['title'])) and not full_table: continue
                product_new['check'] = True
                product_new['positions'].append(variant)
                
            if product_new['check']:
                for variant in product_new['positions']:
                    xlsx_list.write(linecount, 0, product['name'], bold)
                    xlsx_list.write(linecount, 5, product['url'])
                    xlsx_list.write(linecount, 2, ref_prise, italic)
                    xlsx_list.write(linecount, 1, variant['title'])
                    xlsx_list.write(linecount, 3, variant['price'])
                    xlsx_list.write(linecount, 4, 'EU' if variant['eu'] else 'UA')
                    
                    linecount +=1
        progresbar.finish()
        
        try:
            output_table.close()
            print('Таблиця створена'+finish_print)
        except Exception as e:
            print('Таблиця не була створена!'+finish_print)
            with open('errors.txt', 'a') as file:
                file.write(f'\n\n--------------Exception:--------------\n{e}')
            