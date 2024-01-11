import csv

def readcsv(csvfilename, importsource):
    with open('CSA.csv', 'w',newline='\n') as csvoutput:
        fieldnames = ['contacttype','address','info','location','category','organization','source']
        writer = csv.DictWriter(csvoutput, fieldnames=fieldnames)
        writer.writeheader()
        with open(csvfilename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            exclude = ['',' ','\t','\n','-','*','x','no','n/a','N/A','N/a','non','Non','Non.','NONE','no link','no llink','Not available','do.not/have/any/']
            columns = [
                'Email Address',
                'Instagram Link',
                'Twitter Link',
                'Facebook Page Link',
                'Website',
                'LinkedIn Page Link',
                'YouTube Page Link',
                'Vimeo Page Link',
                'Public WhatsApp group link',
                'Public Telegram Group Link',
                #'Other',
                'Discord Server Link',
                'Public Slack Link'
                ]
            typelist = ['MAIL','INSG','TWTR','FCBK','WEBS',"LNIN",'YOUT',"VIME","WHAP","TLGM","DCRD","SLAK"]
            for row in reader:
                if row['Approved'] != 'n':
                    typei = -1
                    for column in columns:
                        typei+=1
                        if row[column] and (row[column] not in exclude):
                            #print(row[column],'\t\t', column)
                            country=''.join([c for c in row['Country'] if ord(c)<0x1f000]).upper().strip()
                            location=''.join([c for c in row['Town (if adding country information please write Country here)'] if ord(c)<0x1f000]).upper().strip()
                            writer.writerow({fieldnames[0]:typelist[typei], fieldnames[1]:row[column], fieldnames[2]:"submitted by: "+row['Your name'],fieldnames[3]:location, fieldnames[4]:country,fieldnames[5]:'',fieldnames[6]:importsource})

                    #print(row['Country'], row['Town (if adding country information please write Country here)'], row['Your name'],'\n')
            
readcsv('CSA List.csv', 'https://docs.google.com/spreadsheets/d/17ADogMNYXGzBBCtLFe7XCl8EBDrZCVExr6KMSV3HwxI')