#!/usr/bin/env python
###############################################################################
# This script takes an MCNP input file, finds the materials card, and then
# coverts all compostions to normalized weight percents. ALARA materials 
# defintions, with everything but density are then written.
#
# input: MCNP input file, optional output file name
# output: ALARA material definations, without density specificed.

from optparse import OptionParser
import linecache

###############################################################################
# This function searchs through inp and returns an array of the line numbers of
# lines that begin with m* where * is a digit, and also an array of mat nums.

def find_mat_lines( inp ) :

    mat_count=0
    line_count=1
    line=linecache.getline(inp,line_count)
    line_array=[]
    mat_nums=[]

    # scroll through every line of the mcnp inp file
    while line != '':

        # check to see if there are characters in line
        if len(line.split()) > 0:

            # check to see if the first string has more than one character
            if len(line.split()[0]) > 1 :

                # check to see if first string is in the form m* where * is a digit
                if line.split()[0][0]=='m' and line.split()[0][1].isdigit() == True:
                    # add line number to line array
                    line_array.append(line_count)   
                    mat_nums.append(line.split()[0][1:])                                    

        line_count += 1
        line=linecache.getline(inp,line_count)

    return line_array, mat_nums

###############################################################################
# This function take a line number and creates an array of data with the
# entries being atomic number xxx, atomic mass xxx and composition

def get_data_array(inp, x) :
   
    
    data=[]
    count = x
    line=linecache.getline(inp,count)
    print x
    # Iterate through the
    while count == x or line.split()[0][0].isdigit() == True:

        # If the first line is in the form mX XXXX XXXX then ignore the mX
        if count==x :
            if len(line.split()) > 1:            
                line_array=line.split()[1:3]
            else :
                count +=1
                line=linecache.getline(inp,count)
                continue
        else :
            line_array=line.split()[0:2]

        # Delete xsdir specification
        if line_array[0].find('.') != -1 :
            line_array[0]=line_array[0].split('.')[0]
       
        # Ensure element name is in ZZZAAA format
        line_array[0]='{0:06d}'.format(int(line_array[0])) 

        # Split ZZZAAA into ZZZ and AAA (adding another column)
        line_array=[int(line_array[0][1:3]),int(line_array[0][3:6]),float(line_array[1])]

        # Add another column: the atomic symbol
        line_array.append(A_to_sym(line_array[0]))
        
        # If element has natural composition, change the AAA to average mass
        if line_array[1]==0:
             line_array[1]=sym_to_nat_abun(line_array[3])

        data.append(line_array)
        count +=1
        line=linecache.getline(inp,count)

        # if the next line has less then 2 strings this materail def is over so
        # the loop is broken, otherwise while isdigit criteria is out of range
        if len(line.split()) < 2 :
            break
  
    return data

###############################################################################
# This function determines if compostions are in weight or atom percent, and 
# then calculates the normalized weight percents accordingly.

def calc_weight_percents(data) :
    product_sum=0
    if str(data[0][2])[0] == '-' :
        for x in data :
            product_sum += x[2]
        for x in data :
            x[2]=x[2]/product_sum*100
 
    else :
        for x in data:
            product_sum += x[2]*x[1]    
        for x in data :
            x[2]=x[2]*x[1]/product_sum*100
    
    return data

###############################################################################
# This funtion prints the ALARA materials definion (everything but density),
# from the data array it receives.

def print_alara_mats(w_percents, mat_num, output) :

   output.write('mat_{0}\t<rho>\t{1}\n'.format(mat_num,len(w_percents)))
   
   for x in w_percents :
       # if single isotope, write in the form sym:AAA
       if type(x[1]) == int :
           output.write('{0}:{1}\t{2:7E}\t{3}\n'.format(x[3], x[1], x[2],x[0]))
       else :
           output.write('{0}\t{1:7E}\t{2}\n'.format(x[3], x[2],x[0]))
   
   output.write('\n')

###############################################################################
# This function returns an atomic symbol from a dictionary based on an atomic
# number.

def A_to_sym(A) :

    sym={1:'h', 2:'he', 3:'li', 4:'be', 5:'b', 6:'c', 7:'n', 8:'o', 9:'f',
         10:'ne', 11:'na', 12:'mg', 13:'al', 14:'si', 15:'p', 16:'s',
         17:'cl', 18:'ar', 19:'k', 20:'ca', 21:'sc', 22:'ti', 23:'v',
         24:'cr', 25:'mn', 26:'fe', 27:'co', 28:'ni', 29:'cu', 30:'zn',
         31:'ga', 32:'ge', 33:'as', 34:'se', 35:'br', 36:'kr', 37:'rb',
         38:'sr', 39:'y', 40:'zr', 41:'nb', 42:'mo', 43:'tc', 44:'ru',
         45:'rh', 46:'pd', 47:'ag', 48:'cd', 49:'in', 50:'sn', 51:'sb',
         52:'te', 53:'i', 54:'xe', 55:'cs', 56:'ba', 57:'la', 58:'ce',
         59:'pr', 60:'nd', 61:'pm', 62:'sm', 63:'eu', 64:'gd', 65:'tb',
         66:'dy', 67:'ho', 68:'er', 69:'tm', 70:'yb', 71:'lu', 72:'hf',
         73:'ta', 74:'w', 75:'re', 76:'os', 77:'ir', 78:'pt', 79:'au',
         80:'hg', 81:'ti', 82:'pb', 83:'bi', 84:'po', 85:'at', 86:'rn',
         87:'fr', 88:'ra', 89:'ac', 90:'th', 91:'pa', 92:'u', 93:'np',
         94:'pu', 95:'am', 96:'cm', 97:'bk', 98:'cf', 99:'es', 100:'fm',
         101:'md', 102:'no', 103:'lr', 104:'rf', 105:'db', 106:'sg',
         107:'bh', 108:'hs', 109:'mt'} 

    return sym[A]

###############################################################################
# This function returns a natural abundance molar mass based on an atomic
# symbol.

def sym_to_nat_abun(sym) :

    nat_abun = {'h':1.0079,'he':4.0026,'o':15.999,'li':6.941,'be':9.0122, 
            'b':10.811,'c':12.011,'n':14.007,'o':15.999,'f':18.998, 'ne':20.180, 
            'na':22.990,'mg':24.305,'al':26.982,'si':28.086,'p':30.974,'s':32.065,
            'cl':35.453,'ar':39.948,'k':39.098,'ca':40.078,'sc':44.956, 
            'ti':47.867,'v':50.942,'cr':51.996,'mn':54.938,'fe':55.845, 
            'co':58.933,'ni':58.693,'cu':63.546,'zn':65.39,'ga':69.723, 
            'ge':72.61,'as':74.922,'se':78.96,'br':79.904, 'kr':83.80, 
            'rb':85.468,'sr':87.62,'y':88.906,'zr':91.224,'nb':92.906, 
            'mo':95.94,'tc':98,'ru':101.07,'rh':102.91,'pd':106.42,'ag':107.87, 
            'cd':112.41,'in':114.82,'sn':118.71,'sb':121.76,'te':127.60, 
            'i':126.90,'xe':131.29,'cs':132.91,'ba':137.33,'la':138.91, 
            'ce':140.12,'pr':140.91,'nd':144.24,'pm':145,'sm':150.36, 
            'eu':151.96,'gd':157.25,'tb':158.93,'dy':162.50,'ho':164.93, 
            'er':167.26,'tm':168.93,'yb':173.04,'lu':174.97,'hf':178.49, 
            'ta':180.95, 'w':183.84,'re':186.21,'os':190.23,'ir':192.22, 
            'pt':195.08,'au':196.97,'hg':200.59,'ti':204.38,'pb':207.2, 
            'bi':208.98,'po':209,'at':210,'rn':222,'fr':223,'ra':226,'ac':227, 
            'th':232.04,'pa':231.04,'u':238.03,'np':237,'pu':244,'am':243, 
            'cm':247,'bk':247,'cf':251,'es':252,'fm':257,'md':258,'no':259, 
            'lr':262,'rf':261,'db':262,'sg':266,'bh':264,'hs':269,'mt':268}

    return nat_abun[sym]

###############################################################################prin

def main( arguments = None ) :

   #Instantiate option parser
    parser = OptionParser\
             (usage='%prog <mcnp_input> [options]')

    parser.add_option('-o', dest='output', default='matlib.out',\
                      help = 'Name of mesh output file, default=%default')

    (opts, args) = parser.parse_args( arguments )

    inp=args[0]

    # find lines of input file that begin mat defs, and also the mat numbers
    mat_lines, mat_nums =find_mat_lines(inp)

    output=file(opts.output, 'w')

    for i, x in enumerate(mat_lines) :
        data=get_data_array(inp,x)
        w_percents=calc_weight_percents(data)
        print_alara_mats(w_percents, mat_nums[i], output)

    output.close()

    print '{0} material definitions written'.format(len(mat_nums))
###############################################################################
if __name__ == '__main__':
    main()
