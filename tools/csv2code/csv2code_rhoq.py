# Original written by Doug Fraker 2018
# this program takes csv output from Tiled
# and turns it into a C style array that can be included
# NES programming...cc65

# Re-written by Seth Gorden 2021
# Reads in a file that determines which pattern values
# are considered collidable.
# Outputs a c-code array of any size map.
# Your collision csv MUST have comma-delimited rows of 0/1 values
# The filename can be changed as need, lutfile is the collision data
# Collision data should correspond to your background pattern table
# 0 = clear, 1 = collidable
# A MetaTile which contains ANY collidable pattern
# will be marked as collidable in the output file

import sys
import csv
import os
import time

program = os.path.basename(__file__)
lutfile = "collision.csv"
promptxt = "Press any key to continue."
output = ""

failed = 0

opt_showcode = 0
opt_verbose = 1
opt_noprompt = 2
opt_noconfirm = 3
opt_oob_empty = 4
options = [0, 0, 0, 0, 0]

args = ["", ""]
flags = ["code", "verbose", "noprompt", "noconfirm", "oob_empty"]
fdesc = ["print c-code after processing", "print all processing messages", "do not request input to continue", "do not print confirmation message after processing", "out of bounds pattern references will be marked as empty (default SOLID)"]

def buildSyntax():
    syntax = "--------------------------------\n"
    syntax += program + " filename.csv"
    for f in range(0, len(options)):
        syntax += " [" + flags[f] + ']'
    syntax += '\n'
    syntax += "--------------------------------\n"
    for f in range(0, len(fdesc)):
        syntax += flags[f] + ": " + fdesc[f]
        if (options[f]):
            syntax += " [DEFAULT]"
        syntax += '\n'
    return syntax

def pause():
    if not checkOption(opt_noprompt):
        input(promptxt)

def checkArg(index):
    value = ""
    try:
        #print("checking system argument index: " + str(index))
        value = sys.argv[index]
        #print("value = " + value)
        return value
    except:
        return None

def InitOptions():
    for a in range(0, len(args)):
        arg_index = a + 2
        args[a] = checkArg(arg_index)
        if (args[a] is None):
            continue
        for f in range(0, len(flags)):
            if str(args[a]) == str(flags[f]):
                options[f] = 1
    #print(str(options))

def checkOption(opt):
    return options[opt] == 1

def safelyGetPattern(col, row, list2D):
    if row >= len(list2D) or col >= len(list2D[row]):
        #print("safelyGetPattern(" + str(col) + ", " + str(row) + ", list2D) was out of bounds!")
        return None
    else:
        return list2D[row][col]

def checkArrayForConsistency(list2D):
    
    row_lengths = [0]
    firstrowlen = len(list2D[0])
    unique_rowlengths = [[0, firstrowlen]]
    
    for r in range(0, len(list2D)):
        thisrowlen = len(list2D[r])
        if r >= len(row_lengths):
            row_lengths.append(thisrowlen)
        else:
            row_lengths[r] = thisrowlen
        
        if thisrowlen != firstrowlen:
            unique_rowlengths.append([r, thisrowlen])

    #if there's more than one record here, we have a jagged array of data.
    #let's warn the user!
    if len(unique_rowlengths) > 1:
        print("WARNING: Irregular rows lengths!")
        for rl in range(0, len(unique_rowlengths)):
            print("    row#" + str(unique_rowlengths[rl][0]) + " has " + str(unique_rowlengths[rl][1]) + " values.")
            if 0 != (unique_rowlengths[rl][0] % 2):
                print("        ERROR: Odd number of values- not compatible with metatiles!")

try:
    filename = sys.argv[1]
except IndexError:
    syntax = buildSyntax()
    print(syntax)
    print("Also, '" + lutfile + "' must be present in order to process your file.")
    pause()
    failed = 1

if failed == 0:
    newname = filename[0:-4] + ".c"
    newname2 = os.path.basename(filename)
    newname2 = newname2[0:-4]

    mt_pat = [0,0,0,0]
    mt_cld = [0,0,0,0]
    solid  = 0

    #open csv map file, and load into 'your_list' 2D array
    try:
        with open(filename, 'r') as csvmap:
            reader = csv.reader(csvmap)
            your_list = list(reader)
            csvmap.close
    except IOError:
        print(program + " failed to open '" + filename + "'.")
        pause()
        failed = 1

    InitOptions()

    if failed == 0:
        #open csv collision look-up table, and load into 'collision_list' 2D array
        try:
            with open(lutfile, 'r') as c_file:
                lutreader = csv.reader(c_file)
                c_list = list(lutreader)
                c_file.close
        except IOError:
            print(program + " failed to load '" + lutfile + "'.\nThis file must be present in the same directory\nin order to process " + filename + '.')
            pause()
            failed = 1

        if failed == 0:
        
            checkArrayForConsistency(your_list)
            #get collision data size
            c_rows = len(c_list)
            c_cols = len(c_list[0])
            c_size = c_rows * c_cols

            if checkOption(opt_verbose):
                print ("Successfully Loaded Collision table of size: (" + str(c_cols) + ',' + str(c_rows) + ')')
                for j in range(0, len(c_list)):
                    print(str(c_list[j]))
                time.sleep(1)

            #open code file into which we'll write the data
            try:
                codefile = open(newname, 'w')  # warning, this may overwrite old file !!!!!!!!!!!!!!!!!!!!!
            except IOError:
                print(program + " failed to open '" + newname + "'. Process aborted.")
                pause()
                failed = 1

            if 0 == failed:
                #setup iteration data
                in_rows = len(your_list)       #total rows in file
                mt_rows = in_rows >> 1         #metatiles are 2x2

                if checkOption(opt_verbose):
                    print("map rows " + str(in_rows))
                    print("mt_rows " + str(mt_rows))

                #write file header
                output += "const unsigned char " + newname2 + "[]=\n{\n"
                
                mtcount = 0

                for row in range (0, mt_rows):
                    codefile.write('\t')
                    
                    in_cols  = len(your_list[row])  #total numbers in row
                    mt_cols = in_cols >> 1          #metatiles are 2x2
                    
                    if checkOption(opt_verbose):
                        print("row #" + str(row) +": map cols " + str(in_cols) + ", mt_cols " + str(mt_cols))
                    
                    for col in range (0, mt_cols):
                        
                        if checkOption(opt_verbose):
                            print ("    Metatile #" + str(mtcount+1) + " @ (" + str(col) + ',' + str(row) + ')')
                            
                        inrow = row << 1
                        incol = col << 1
                        
                        mt_pat[0] = safelyGetPattern(incol, inrow, your_list)
                        mt_pat[1] = safelyGetPattern(incol+1, inrow, your_list)
                        mt_pat[2] = safelyGetPattern(incol, inrow+1, your_list)
                        mt_pat[3] = safelyGetPattern(incol+1, inrow+1, your_list)
                        
                        if checkOption(opt_verbose):
                            print("        patterns [" + str(mt_pat[0]) + ',' + str(mt_pat[1]) + ',' + str(mt_pat[2]) + ',' + str(mt_pat[3]) + ']')

                        # Determine whether the metatile is solid
                        mt_cld = [0,0,0,0]
                        solid = 0;
                        for p in range(0, len(mt_pat)):
                        
                            if None == mt_pat[p]:
                                print ("    ERROR: Metatile #" + str(mtcount+1) + " @ (" + str(col) + ',' + str(row) + ") is missing data.\n        Check your file for irregular row-length or bad data.")
                                continue
                        
                            pat = int(mt_pat[p])
                            pat_x = int(pat % c_cols)
                            pat_y = int(pat / c_cols)
                            
                            #bounds check
                            if pat >= c_size:
                                print("    ERROR: pattern #" + str(pat) + " @ row:" + str(pat_y) + ', col:' + str(pat_x) + " is out of bounds for the given collision data!"); 
                                if not checkOption(opt_oob_empty):
                                    print("           Metatile will be marked as SOLID.");
                                    solid = 1
                                    time.sleep(1)
                                    break
                                else:
                                    print("           pattern will be considered empty.");
                                    time.sleep(1)
                            else:                            
                                mt_cld[p] = int(c_list[pat_y][pat_x])
                                
                                if checkOption(opt_verbose):
                                    print("        pat #" + str(pat) + " @ row:" + str(pat_y) + ', col:' + str(pat_x) + " | " + str(mt_cld[p]))
                                
                                if mt_cld[p] == 1:
                                    if checkOption(opt_verbose):
                                        print("        SOLID")
                                    solid = 1
                                    break
                        
                        if checkOption(opt_verbose) and int(solid) == 0:
                            print("        empty")
                        
                        #write value
                        output += str(solid)
                        
                        # comma delimiter after every value except the last
                        if (mt_cols-1) != col or (mt_rows-1) != row:
                            output += ","
                            
                        mtcount = mtcount + 1

                    output += "\n"

                output += "};\n"
                
                if checkOption(opt_showcode) or checkOption(opt_verbose):
                    print(output)
                    
                codefile.write(output)
                codefile.close()
                
                if not checkOption(opt_noconfirm):
                    print(newname + " written succesfully.")
                pause()
