import sympy
import numpy as np
#sympy.init_printing(use_unicode=True)

x_s, y_s, z_s = sympy.symbols('x_s y_s z_s')
x_sp, y_sp, z_sp = sympy.symbols('x_sp y_sp z_sp')
x_o, y_o, z_o = sympy.symbols('x_o y_o z_o')
x_p, y_p, z_p = sympy.symbols('x_p y_p z_p')
x_f, y_f, z_f = sympy.symbols('x_f y_f z_f')
d, r, t_1 = sympy.symbols('d r t_1')
t_0 = sympy.symbols('t_0', nonnegative=True)

# 2D : infinitely tall objects

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


# Full 3D projection 

eq_line_FO_x = sympy.Eq(x_s, x_f + (x_o - x_f) * t_0)
eq_line_FO_y = sympy.Eq(y_s, y_f + (y_o - y_f) * t_0)
eq_line_FO_z = sympy.Eq(z_s, z_f + (z_o - z_f) * t_0)
eq_cylinder = sympy.Eq(x_s*x_s + y_s*y_s, r*r)
eq_line_SP_x = sympy.Eq(x_sp, x_s + (x_p - x_s) * t_1)
eq_line_SP_y = sympy.Eq(y_sp, y_s + (y_p - y_s) * t_1)
eq_line_SP_z = sympy.Eq(z_sp, z_s + (z_p - z_s) * t_1)
eq_screen_plane = sympy.Eq(x_sp, -r)
eq_proj_x = sympy.Eq(x_p, -d)
eq_proj_y = sympy.Eq(y_p, 0)
eq_proj_z = sympy.Eq(z_p, 0)

solutions = sympy.solve(
    [
        eq_line_FO_x,
        eq_line_FO_y,
        eq_line_FO_z,
        eq_cylinder,
        eq_line_SP_x,
        eq_line_SP_y,
        eq_line_SP_z,
        eq_screen_plane,
        eq_proj_x,
        eq_proj_y,
        eq_proj_z
    ], 
    [y_sp, z_sp, t_1, x_p, y_p, z_p, z_s, x_sp, x_s, y_s, t_0],
    dict=True
)

# try to get only one sol

eq_line_FO_x = sympy.Eq(x_s, x_f + (x_o - x_f) * t_0)
eq_line_FO_y = sympy.Eq(y_s, y_f + (y_o - y_f) * t_0)
eq_line_FO_z = sympy.Eq(z_s, 0)
eq_cylinder = sympy.Eq(x_s*x_s + y_s*y_s, r*r)

solutions = sympy.solve(
    [
        eq_line_FO_x,
        eq_line_FO_y,
        eq_line_FO_z,
        eq_cylinder,
    ], 
    [z_s, x_s, y_s, t_0],
    dict=True
)

# TODO: additional constraints: 
# F has to be inside the cylinder
# F and O cannot be in the same location 
