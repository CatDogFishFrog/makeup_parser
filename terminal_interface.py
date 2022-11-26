import argparse
import textwrap
import make_xlsx

def main():
    parser = argparse.ArgumentParser(description=textwrap.dedent('''\
                                    Створення таблиці з обраних товарів з сайту makeup.com.ua.
                                    --------------------------------
                                    Вхідні данні:    
                                        Вхідна таблиця повинна бути у форматі .csv (Comma-separated values)
                                        Для цього у Excel при збереженні таблиці треба обрати цей формат
                                        
                                        Один рядок - один товар.
                                        Перший стовпець: Посилання на товар (https://makeup.com.ua/ua/product/891656/) 
                                        Другий стовпець: Поки що не використовується
                                        Третій стовпець: Ref Price USD
                                        Четвертий стовпець: Ref Price UAH
                                        (якщо введено обидва значення Ref Price, то використовується тільки USD)
                                        
                                        По стандарту шлях до вхідного файлу буде у теці з програмою, а його назва буде input_table.csv.
                                        Шлях та назву файлу можна змінити
                                    
                                    Вихідні данні:
                                        Результат записано у таблицю формату .xlsx
                                        Таблиця буде мати тільки ті позиції, ціна яких менша за Ref Price
                                        
                                        По стандарту шлях до вхідного файлу буде у теці з програмою, а його назва буде out_table.xlsx.
                                        Шлях та назву файлу можна змінити
                                    '''),
                                    formatter_class=argparse.RawDescriptionHelpFormatter,
                                    usage='create [options]',
                                    argument_default=False
                                    )
    parser.add_argument('--start', '-s',
                            help="Почати створення таблиці. Приклад: create.exe -s",
                            action='store_true',
                            required=False
                            )
    
    parser.add_argument('--path_in', '-pi',
                        help='(Опціонально) Обрати розташування файлу з вхідною таблицею. Приклад 1: create.exe -s -pi "C:\\Users\Public\\Documents\\input.csv", Приклад 2: create.exe -s -p input.csv',
                        default='input_table.csv',
                        type=str,
                        required=False
                        )
    parser.add_argument('--path_out', '-po',
                        help='(Опціонально) Обрати розташування файлу з вихідною таблицею. Приклад 1: create.exe -s -po "C:\\Users\Public\\Documents\\output.xlsx", Приклад 2: create.exe -s -po output.xlsx',
                        default='out_table.xlsx',
                        type=str,
                        required=False
                        )
    parser.add_argument('--full', '-f',
                            help=".(Опціонально) Якщо додати цей тег, то виведе повну таблицю, без перевірок на ціну. Приклад: create.exe -s -f",
                            action='store_true',
                            required=False
                            )


    args = parser.parse_args()
    
    if args.start != False:
        make_xlsx.make_xlsx(args.path_in, args.path_out, args.full)
    
    
    
if __name__ == '__main__': main()
