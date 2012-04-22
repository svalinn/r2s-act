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
    
    # Iterate through the
    while count == x or line.split()[0][0].isdigit() == True:

        # If the first line is in the form mX XXXX XXXX then ignore the mX
        if count==x and len(line.split()) > 1:
            line_array=line.split()[1:3]
        else :
            line_array=line.split()[0:2]

        # Delete xslib specification
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

    sym={1:'H', 2:'He', 3:'Li', 4:'Be', 5:'B', 6:'C', 7:'N', 8:'O', 9:'F',
         10:'Ne', 11:'Na', 12:'Mg', 13:'Al', 14:'Si', 15:'P', 16:'S',
         17:'Cl', 18:'Ar', 19:'K', 20:'Ca', 21:'Sc', 22:'Ti', 23:'V',
         24:'Cr', 25:'Mn', 26:'Fe', 27:'Co', 28:'Ni', 29:'Cu', 30:'Zn',
         31:'Ga', 32:'Ge', 33:'As', 34:'Se', 35:'Br', 36:'Kr', 37:'Rb',
         38:'Sr', 39:'Y', 40:'Zr', 41:'Nb', 42:'Mo', 43:'Tc', 44:'Ru',
         45:'Rh', 46:'Pd', 47:'Ag', 48:'Cd', 49:'In', 50:'Sn', 51:'Sb',
         52:'Te', 53:'I', 54:'Xe', 55:'Cs', 56:'Ba', 57:'La', 58:'Ce',
         59:'Pr', 60:'Nd', 61:'Pm', 62:'Sm', 63:'Eu', 64:'Gd', 65:'Tb',
         66:'Dy', 67:'Ho', 68:'Er', 69:'Tm', 70:'Yb', 71:'Lu', 72:'Hf',
         73:'Ta', 74:'W', 75:'Re', 76:'Os', 77:'Ir', 78:'Pt', 79:'Au',
         80:'Hg', 81:'Tl', 82:'Pb', 83:'Bi', 84:'Po', 85:'At', 86:'Rn',
         87:'Fr', 88:'Ra', 89:'Ac', 90:'Th', 91:'Pa', 92:'U', 93:'Np',
         94:'Pu', 95:'Am', 96:'Cm', 97:'Bk', 98:'Cf', 99:'Es', 100:'Fm',
         101:'Md', 102:'No', 103:'Lr', 104:'Rf', 105:'Db', 106:'Sg',
         107:'Bh', 108:'Hs', 109:'Mt'} 

    return sym[A]

###############################################################################
# This function returns a natural abundance molar mass based on an atomic
# symbol.

def sym_to_nat_abun(sym) :

    nat_abun = {'H':1.0079,'He':4.0026,'O':15.999,'Li':6.941,'Be':9.0122, 
            'B':10.811,'C':12.011,'N':14.007,'O':15.999,'F':18.998, 'Ne':20.180, 
            'Na':22.990,'Mg':24.305,'Al':26.982,'Si':28.086,'P':30.974,'S':32.065,
            'Cl':35.453,'Ar':39.948,'K':39.098,'Ca':40.078,'Sc':44.956, 
            'Ti':47.867,'V':50.942,'Cr':51.996,'Mn':54.938,'Fe':55.845, 
            'Co':58.933,'Ni':58.693,'Cu':63.546,'Zn':65.39,'Ga':69.723, 
            'Ge':72.61,'As':74.922,'Se':78.96,'Br':79.904, 'Kr':83.80, 
            'Rb':85.468,'Sr':87.62,'Y':88.906,'Zr':91.224,'Nb':92.906, 
            'Mo':95.94,'Tc':98,'Ru':101.07,'Rh':102.91,'Pd':106.42,'Ag':107.87, 
            'Cd':112.41,'In':114.82,'Sn':118.71,'Sb':121.76,'Te':127.60, 
            'I':126.90,'Xe':131.29,'Cs':132.91,'Ba':137.33,'La':138.91, 
            'Ce':140.12,'Pr':140.91,'Nd':144.24,'Pm':145,'Sm':150.36, 
            'Eu':151.96,'Gd':157.25,'Tb':158.93,'Dy':162.50,'Ho':164.93, 
            'Er':167.26,'Tm':168.93,'Yb':173.04,'Lu':174.97,'Hf':178.49, 
            'Ta':180.95, 'W':183.84,'Re':186.21,'Os':190.23,'Ir':192.22, 
            'Pt':195.08,'Au':196.97,'Hg':200.59,'Ti':204.38,'Pb':207.2, 
            'Bi':208.98,'Po':209,'At':210,'Rn':222,'Fr':223,'Ra':226,'Ac':227, 
            'Th':232.04,'Pa':231.04,'U':238.03,'Np':237,'Pu':244,'Am':243, 
            'Cm':247,'Bk':247,'Cf':251,'Es':252,'Fm':257,'Md':258,'No':259, 
            'Lr':262,'Rf':261,'Db':262,'Sg':266,'Bh':264,'Hs':269,'Mt':268}

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
