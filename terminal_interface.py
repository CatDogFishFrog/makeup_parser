import argparse
import textwrap
import make_xlsx

description_text =   '''Створення таблиці з обраних товарів з сайту makeup.com.ua.
                        ------------------------------------------
                        Вхідні данні:    
                            Вхідна таблиця повинна бути у форматі .csv (Comma-separated values)
                            Для цього у Excel при збереженні таблиці треба обрати цей формат

                            Один рядок - один товар.
                            
                            Перший стовпець: Посилання на товар. 
                                                Приклад: https://makeup.com.ua/ua/product/891656/

                            Другий стовпець: В одному посиланні може бути декілька варіантів товару,
                                                тому, якщо хочете, у цей стовпець можна записати назву
                                                одного з варіантів (або його номер, або частинку назви.
                                                Головне, щоб цей запис був хоч десь у назві та міг відрізнити цого від інших).

                            Третій стовпець: Ref Price USD (розрахунок іде в USD, тому ця ціна буде
                                                переведена у гривні за курсом
                                            сайту https://obmennovosti.info/city.php?city=45)

                            Четвертий стовпець: Ref Price UAH

                            (якщо введено обидва значення Ref Price, то використовується тільки USD)

                            По стандарту шлях до вхідного файлу буде у теці з програмою, а його назва буде input_table.csv.
                            Шлях та назву файлу можна змінити
                        
                        Вихідні данні:
                            Результат записано у таблицю формату .xlsx
                            Таблиця буде мати тільки ті позиції, ціна яких менша за Ref Price

                            По стандарту шлях до вхідного файлу буде у теці з програмою, а його назва буде out_table.xlsx.
                            Шлях та назву файлу можна змінити
                        '''

def main():
    argument_parser = argparse.ArgumentParser(description=textwrap.dedent(description_text),
                                    formatter_class=argparse.RawDescriptionHelpFormatter,
                                    usage='create [options]',
                                    argument_default=False
                                    )
    argument_parser.add_argument('--start', '-s',
                            help="Почати створення таблиці. Приклад: create.exe -s",
                            action='store_true',
                            required=False
                            )
    
    argument_parser.add_argument('--path_in', '-pi',
                        help='(Опціонально) Обрати розташування файлу з вхідною таблицею. Приклад 1: create.exe -s -pi "C:\\Users\\Public\\Documents\\input.csv", Приклад 2: create.exe -s -p input.csv',
                        default='input_table.csv',
                        type=str,
                        required=False
                        )
    argument_parser.add_argument('--path_out', '-po',
                        help='(Опціонально) Обрати розташування файлу з вихідною таблицею. Приклад 1: create.exe -s -po "C:\\Users\\Public\\Documents\\output.xlsx", Приклад 2: create.exe -s -po output.xlsx',
                        default='out_table.xlsx',
                        type=str,
                        required=False
                        )


    arguments = argument_parser.parse_args()
    
    if arguments.start:
        make_xlsx.process_product_list(arguments.path_in, arguments.path_out)
    
    
    
if __name__ == '__main__': main()
