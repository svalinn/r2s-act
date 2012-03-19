#!/usr/bin/env python
#Filename:array_create.py
#This is a script for converting a line to a list by eliminating whitespace
#The inputs are the lines, an list of the desired columns, and an list of types

def convert(line, columns, types, delimiter):
    char_count=0
    column_list=[0]*len(columns)
    column_count=0;

    while char_count<len(line)-1:
        if line[char_count] not in delimiter:
            min_char = char_count
            while char_count<len(line)-1 and line[char_count] not in delimiter:
                char_count=char_count +1
            max_char=char_count

            if column_count+1 in columns:
                if types[columns.index(column_count+1)] == 'int':
                    value=int(line[min_char:max_char])
                if types[columns.index(column_count+1)]== 'float':
                    value=float(line[min_char:max_char])
                if types[columns.index(column_count+1)] == 'str':
                    value=str(line[min_char:max_char])                 
                column_list[columns.index(column_count+1)]=value
            column_count=column_count+1
        char_count=char_count+1

    return column_list

#import linecache

#Data=linecache.getline('testing/test_line_to_list_data', 1)
#a=convert(Data, [8,9,10,7,6,5,4,3,2,1], ['float','str','int','int','int','int','int','int','int', 'str'], (' ','\t') )
#print a
