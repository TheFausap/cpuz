import random
import os

PSIZ   = 0x64
SSIZ   = 0x1FFF
ORGZ   = 0x12C
PRAREA = 0xC8
PRSIZ  = 0x50

mem = [0] * SSIZ
pmem = [0] * PSIZ

r0 = 0
r1 = 0
r2 = 0
r3 = 0
r4 = 0
r5 = 0
# try to avoid a direct usage of the registers below
r6 = 0  # special register overwritten if overflow happens
r7 = 0  # special register overwritten if overflow happens
        # used also in IDIV operation, getting the remainder

ir = 0

fl = 0
imm = 0
ac = random.randint(1, 32766)

pc = 0
sp = SSIZ - 1
ppos = PRAREA

prog = open('test.mem', 'r')
prt = open('printer.txt','w')
lines = prog.readlines()


def push1(v):
    # internal op
    global sp
    mem[sp] = v
    sp = sp - 1


def pop1():
    # internal op
    global sp
    sp = sp + 1
    return mem[sp]


def rebase(v):
    # internal op
    vr = v + ORGZ
    return vr


def ni():
    global pc
    pc = pc + 1


# FLAG OPS

def clu():
    # ic = 0x15
    global fl
    fl = fl ^ 0x04


def seu():
    # ic = 0x16
    global fl
    fl = fl | 0x04


def clv():
    # ic = 0x10
    global fl
    fl = fl & 0x05


def clz():
    # ic = 0x11
    global fl
    fl = fl ^ 0x01


def sev():
    # ic = 0x12
    global fl
    fl = fl | 0x02


def sez():
    # ic = 0x13
    global fl
    fl = fl | 0x01


def cla():
    # ic = 0x14
    global ac
    ac = 0
    ni()


# END FLAG OPS

def chkflu16():
    # internal op
    global r0
    global r7
    global r6
    global ac
    global fl

    if ac == 0:
        sez()

"""
    if ac > 0xffffffffffffffff:
        sev()
    if ac < -0xffffffffffffffff:
        seu()
    if (fl & 2) == 2:
        r7 = (r6 + r7 + (ac >> 64))
        ac = ac & 0xffffffffffffffff
"""



def chkfl16():
    # internal op
    # signed version
    global r0
    global r7
    global r6
    global fl
    global ac
    if ac == 0:
        sez()
    if ac > 32767:
        sev()
    if ac < -32768:
        seu()
    if (fl & 2) == 2:
        r7 = (r6 + r7 + (ac >> 16))
        ac = ac & 0xffff


def u2s(n):
    # internal op
    # do not set flags
    if n > 32767:
        n = n & 0x7fff
    if n < -32768:
        n = n & 0x7fff
    return n


def nop():
    # ic = 0x00
    ni()


def ldir0():
    # ic = 0x01
    global r0
    v = pop1()
    r0 = v
    ni()


def loa():
    # ic = 0x02
    global pc
    ni()
    push1(mem[pc])
    ni()


def ldm():
    # ic = 0x03
    global r0
    v = pop1()
    r0 = mem[rebase(v)]
    ni()


def sto():
    # ic = 0x04
    global r0
    v = pop1()
    mem[rebase(v)] = r0
    ni()


def incr0():
    # ic = 0x05
    # set flags, but do not consider them in the increment
    global r0
    r0 = r0 + 1
    # chkflu16()
    ni()


def decr0():
    # ic = 0x06
    # set flags, but do not consider them in the decrement
    global r0
    r0 = r0 - 1
    # chkflu16()
    ni()


def adi():
    # ic = 0x07
    global ac
    v = pop1()
    ac = ac + v
    chkflu16()
    ni()


# print("adi - " + str(pc))

def addm():
    # ic = 0x08
    global ac
    v = pop1()
    ac = ac + mem[rebase(v)]
    chkflu16()
    ni()


def sbi():
    # ic = 0x09
    global ac
    v = pop1()
    ac = ac - v
    chkflu16()
    ni()


def subm():
    # ic = 0x0A
    global ac
    v = pop1()
    ac = ac - mem[rebase(v)]
    chkflu16()
    ni()


def mui():
    # ic = 0x0B
    global ac
    v = pop1()
    ac = ac * v
    chkflu16()
    ni()


def idivi():
    # ic = 0x0C
    global ac
    global r7
    v = pop1()
    ac, r7 = divmod(ac,v)
    chkflu16()
    ni()


def idivm():
    # ic = 0x0C
    global ac
    global r7
    v = pop1()
    ac, r7 = divmod(ac,mem[rebase(v)])
    chkflu16()
    ni()


def mulm():
    # ic = 0x0C
    global ac
    v = pop1()
    ac = ac * mem[rebase(v)]
    chkflu16()
    ni()


def adis():
    # ic = 0x20
    global ac
    v = pop1()
    v = u2s(v)
    ac = ac + v
    chkfl16()
    ni()


def addms():
    # ic = 0x21
    global ac
    v = pop1()
    ac = ac + mem[v]
    chkfl16()


def sbis():
    # ic = 0x22
    global ac
    v = pop1()
    ac = ac - v
    chkfl16()


def subms():
    # ic = 0x23
    global ac
    v = pop1()
    ac = ac - mem[v]
    chkfl16()


def muis():
    # ic = 0x24
    global ac
    v = pop1()
    ac = ac * v
    chkfl16()


def mulms():
    # ic = 0x25
    global ac
    v = pop1()
    ac = ac * mem[v]
    chkfl16()


def jmp():
    # ic = 0x30
    global pc
    ni()
    pc = mem[pc]


def ldir1():
    # ic = 0x31
    global r1
    v = pop1()
    r1 = v
    ni()


def jzr():
    # ic = 0x32
    global pc
    ni()
    if r0 == 0:
        pc = mem[pc]
    else:
        ni()


def jz():
    # ic = 0x33
    global pc
    ni()
    if (fl & 0x0001) == 1:
        pc = mem[pc]
    else:
        ni()

def jgt():
    # ic = 0x36
    global pc
    ni()
    if r0 > r1:
        pc = mem[pc]
    else:
        ni()


def outp():
    # ic = 0xe0
    global ppos
    for x in range(PRAREA,ppos,1):
        prt.write(str(mem[x]))
        prt.write("\n")
    prt.flush()
    os.fsync(prt.fileno())
    ppos = PRAREA


def stpr():
    #ic = 0xe1
    global ac
    global ppos
    if ppos > PRAREA+PRSIZ:
        outp()
    mem[ppos] = ac
    ppos = ppos + 1
    ni()


def str6pr():
    #ic = 0xe2
    global r6
    global ppos
    if ppos > PRAREA+PRSIZ:
        outp()
    mem[ppos] = r6
    ppos = ppos + 1
    ni()


def str7pr():
    #ic = 0xe3
    global r7
    global ppos
    if ppos > PRAREA+PRSIZ:
        outp()
    mem[ppos] = r7
    ppos = ppos + 1
    ni()


def cpyr0():
    # ic = 0xf0
    global ac
    global r0
    global r7
    global r6
    global fl
    if (fl & 0x02) == 2:
        r6 = r7
    r0 = ac
    ni()


def cpyr1():
    # ic = 0xf1
    global ac
    global r1
    global r7
    global r6
    global fl
    if (fl & 0x02) == 2:
        r6 = r7
    r1 = ac
    ni()


def cpyr2():
    # ic = 0xf2
    global ac
    global r2
    global r7
    global r6
    global fl
    if (fl & 0x02) == 2:
        r6 = r7
    r2 = ac
    ni()


def lor0():
    # ic = 0xf3
    global r0
    push1(r0)
    ni()


def lor1():
    # ic = 0xf4
    global r1
    push1(r1)
    ni()


def lor2():
    # ic = 0xf5
    global r2
    push1(r2)
    ni()


def incr1():
    # ic = 0xf6
    global r1
    r1 = r1 + 1
    ni()


def incr2():
    # ic = 0xf7
    global r2
    r2 = r2 + 1
    ni()


def decr1():
    # ic = 0xf8
    global r1
    r1 = r1 - 1
    ni()


def decr2():
    # ic = 0xf9
    global r2
    r2 = r2 - 1
    ni()


def ldir2():
    # ic = 0xfa
    global r2
    v = pop1()
    r2 = v
    ni()


def ldir3():
    # ic = 0xfb
    global r3
    v = pop1()
    r3 = v
    ni()


def lor3():
    # ic = 0xfc
    global r3
    push1(r3)
    ni()


def lor6():
    # ic = 0xfd
    global r6
    push1(r6)
    ni()


def lor7():
    # ic = 0xfe
    global r7
    push1(r7)
    ni()


def hlt():
    # ic = 0xff
    global pc
    pc = -1


def exe(lin):
    ic = lin
    # print("Executing PC: " + str(pc) + " - " + str(lin))
    if ic == 0:
        print("nop")
        nop()
    elif ic == 1:
        print("ldir0")
        ldir0()
    elif ic == 2:
        print("loa")
        loa()
    elif ic == 3:
        print("ldm")
        ldm()
    elif ic == 4:
        print("sto")
        sto()
    elif ic == 5:
        print("incr0")
        incr0()
    elif ic == 6:
        print("decr0")
        decr0()
    elif ic == 7:
        print("adi")
        adi()
    elif ic == 8:
        print("addm")
        addm()
    elif ic == 9:
        print("sbi")
        sbi()
    elif ic == 10:
        print("subm")
        subm()
    elif ic == 11:
        print("mui")
        mui()
    elif ic == 12:
        print("mulm")
        mulm()
    elif ic == 13:
        print("idivi")
        idivi()
    elif ic == 16:
        print("clv")
        clv()
        ni()
    elif ic == 17:
        print("clz")
        clz()
        ni()
    elif ic == 18:
        print("sev")
        sev()
        ni()
    elif ic == 19:
        print("sez")
        sez()
        ni()
    elif ic == 20:
        print("cla")
        cla()
    elif ic == 32:
        print("adiS")
        adis()
    elif ic == 33:
        print("addmS")
        addms()
    elif ic == 34:
        print("sbiS")
        sbis()
    elif ic == 35:
        print("muiS")
        muis()
    elif ic == 36:
        print("mulmS")
        mulms()
    elif ic == 48:
        print("jmp")
        jmp()
    elif ic == 49:
        print("ldir1")
        ldir1()
    elif ic == 50:
        print("jzr")
        jzr()
    elif ic == 51:
        print("jz")
        jz()
    elif ic == 52:
        print("jge")
        jge()
    elif ic == 53:
        print("jle")
        jle()
    elif ic == 54:
        print("jgt")
        jgt()
    elif ic == 55:
        print("jlt")
        jlt()
    elif ic == 56:
        print("jnzr")
        jnzr()
    elif ic == 57:
        print("jnz")
        jnz()
    elif ic == 58:
        print("jv")
        jv()
    elif ic == 59:
        print("ju")
        ju()
    elif ic == 224:
        print("outp")
        outp()
        ni()
    elif ic == 225:
        print("stpr")
        stpr()
    elif ic == 226:
        print("str6pr")
        str6pr()
    elif ic == 227:
        print("str7pr")
        str7pr()
    elif ic == 240:
        print("cpyr0")
        cpyr0()
    elif ic == 241:
        print("cpyr1")
        cpyr1()
    elif ic == 242:
        print("cpyr2")
        cpyr2()
    elif ic == 243:
        print("lor0")
        lor0()
    elif ic == 244:
        print("lor1")
        lor1()
    elif ic == 245:
        print("lor2")
        lor2()
    elif ic == 246:
        print("incr1")
        incr1()
    elif ic == 247:
        print("incr2")
        incr2()
    elif ic == 248:
        print("decr1")
        decr1()
    elif ic == 249:
        print("decr2")
        decr2()
    elif ic == 250:
        print("ldir2")
        ldir2()
    elif ic == 251:
        print("ldir3")
        ldir3()
    elif ic == 252:
        print("lor3")
        lor3()
    elif ic == 253:
        print("lor6")
        lor6()
    elif ic == 254:
        print("lor7")
        lor7()
    elif ic == 255:
        print("hlt")
        hlt()
    else:
        print("inv")
        nop()


def prnflg():
    if fl == 0:
        return "---"
    elif fl == 1:
        return "--Z"
    elif fl == 2:
        return "-V-"
    elif fl == 3:
        return "-VZ"
    elif fl == 4:
        return "U--"
    elif fl == 5:
        return "U-Z"
    elif fl == 6:
        return "UV-"
    elif fl == 7:
        return "UVZ"
    else:
        return "uknf"


def dbg():
    # print(pmem)
    # print(mem)
    print("\nPC:" + str(pc))
    print("PRSTART:" + str(PRAREA))
    print("PREND:" + str(ppos) + "\n")
    print("AC:" + str(ac))
    print("R0:" + str(r0))
    print("R1:" + str(r1))
    print("R2:" + str(r2))
    print("R3:" + str(r3))
    print("R4:" + str(r4))
    print("R5:" + str(r5))
    print("R6:" + str(r6))
    print("R7:" + str(r7))
    print("FL:" + str(fl) + "(" + prnflg() + ")")


def load():
    global pc
    global pmem

    prt.seek(0,0)
    count = 0
    for lin in lines:
        mem[count] = int(lin.strip())
        count = count + 1
        if count > int(SSIZ / 2):
            print("0pbig")
            prog.close()
            exit(-1)

    while pc != -1:
        exe(mem[pc])
        dbg()
        # print(pc)
        # input("next step...")


load()
prog.close()
prt.close()
