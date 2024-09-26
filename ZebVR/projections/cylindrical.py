import sympy
import numpy as np
#sympy.init_printing(use_unicode=True)

x_s, y_s, x_sp, y_sp, x_o, y_o, x_f, y_f, d, r = sympy.symbols('x_s y_s x_sp y_sp x_o y_o x_f y_f d r')

eq_circle = sympy.Eq(x_s*x_s + y_s*y_s, r*r)
eq_line = sympy.Eq((y_s - y_f), ((y_o - y_f)/(x_o - x_f)) * (x_s - x_f))
eq_thales = sympy.Eq((y_s / (d+x_s)), (y_sp/(d-r)))
constraint = sympy.Ge((x_o - x_f)*(x_s - x_f) + (y_o - y_f)*(y_s - y_f), 0)

solutions = sympy.solve([eq_circle, eq_line, eq_thales], [y_sp, y_s, x_s], dict=True)

def transform(r, d, x_o, y_o, x_f, y_f):
    y0 = -(-d + r) * (
        - d*x_f**2*y_o 
        + d*x_f*x_o*y_f 
        + d*x_f*x_o*y_o 
        - d*x_o**2*y_f 
        + d*y_f*np.sqrt(r**2*x_f**2 - 2*r**2*x_f*x_o + r**2*x_o**2 + r**2*y_f**2 - 2*r**2*y_f*y_o + r**2*y_o**2 - x_f**2*y_o**2 + 2*x_f*x_o*y_f*y_o - x_o**2*y_f**2) 
        - d*y_o*np.sqrt(r**2*x_f**2 - 2*r**2*x_f*x_o + r**2*x_o**2 + r**2*y_f**2 - 2*r**2*y_f*y_o + r**2*y_o**2 - x_f**2*y_o**2 + 2*x_f*x_o*y_f*y_o - x_o**2*y_f**2) 
        + r**2*x_f*y_f 
        - r**2*x_f*y_o 
        - r**2*x_o*y_f 
        + r**2*x_o*y_o 
        - x_f*y_o*np.sqrt(r**2*x_f**2 - 2*r**2*x_f*x_o + r**2*x_o**2 + r**2*y_f**2 - 2*r**2*y_f*y_o + r**2*y_o**2 - x_f**2*y_o**2 + 2*x_f*x_o*y_f*y_o - x_o**2*y_f**2) 
        + x_o*y_f*np.sqrt(r**2*x_f**2 - 2*r**2*x_f*x_o + r**2*x_o**2 + r**2*y_f**2 - 2*r**2*y_f*y_o + r**2*y_o**2 - x_f**2*y_o**2 + 2*x_f*x_o*y_f*y_o - x_o**2*y_f**2)
    ) / (
        -d**2*x_f**2 
        + 2*d**2*x_f*x_o 
        - d**2*x_o**2 
        - d**2*y_f**2 
        + 2*d**2*y_f*y_o 
        - d**2*y_o**2 
        + 2*d*x_f*y_f*y_o 
        - 2*d*x_f*y_o**2 
        - 2*d*x_o*y_f**2 
        + 2*d*x_o*y_f*y_o 
        + r**2*x_f**2 
        - 2*r**2*x_f*x_o 
        + r**2*x_o**2 
        - x_f**2*y_o**2 
        + 2*x_f*x_o*y_f*y_o 
        - x_o**2*y_f**2
    )
    y1 = -(-d + r) * ( 
        - d*x_f**2*y_o 
        + d*x_f*x_o*y_f 
        + d*x_f*x_o*y_o 
        - d*x_o**2*y_f 
        - d*y_f*np.sqrt(r**2*x_f**2 - 2*r**2*x_f*x_o + r**2*x_o**2 + r**2*y_f**2 - 2*r**2*y_f*y_o + r**2*y_o**2 - x_f**2*y_o**2 + 2*x_f*x_o*y_f*y_o - x_o**2*y_f**2) 
        + d*y_o*np.sqrt(r**2*x_f**2 - 2*r**2*x_f*x_o + r**2*x_o**2 + r**2*y_f**2 - 2*r**2*y_f*y_o + r**2*y_o**2 - x_f**2*y_o**2 + 2*x_f*x_o*y_f*y_o - x_o**2*y_f**2) 
        + r**2*x_f*y_f 
        - r**2*x_f*y_o 
        - r**2*x_o*y_f 
        + r**2*x_o*y_o 
        + x_f*y_o*np.sqrt(r**2*x_f**2 - 2*r**2*x_f*x_o + r**2*x_o**2 + r**2*y_f**2 - 2*r**2*y_f*y_o + r**2*y_o**2 - x_f**2*y_o**2 + 2*x_f*x_o*y_f*y_o - x_o**2*y_f**2) 
        - x_o*y_f*np.sqrt(r**2*x_f**2 - 2*r**2*x_f*x_o + r**2*x_o**2 + r**2*y_f**2 - 2*r**2*y_f*y_o + r**2*y_o**2 - x_f**2*y_o**2 + 2*x_f*x_o*y_f*y_o - x_o**2*y_f**2)
    ) / (
        - d**2*x_f**2 
        + 2*d**2*x_f*x_o 
        - d**2*x_o**2 
        - d**2*y_f**2 
        + 2*d**2*y_f*y_o 
        - d**2*y_o**2 
        + 2*d*x_f*y_f*y_o 
        - 2*d*x_f*y_o**2 
        - 2*d*x_o*y_f**2 
        + 2*d*x_o*y_f*y_o 
        + r**2*x_f**2 
        - 2*r**2*x_f*x_o 
        + r**2*x_o**2 
        - x_f**2*y_o**2 
        + 2*x_f*x_o*y_f*y_o 
        - x_o**2*y_f**2
    )
    return (y0, y1)

x, y = np.mgrid[-20:-10,10:20]

transform(30, 100, x, y, 10, -10)
