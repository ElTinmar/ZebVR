import sympy
import numpy as np

# declare symbols ------------------------------------

x_o, y_o, z_o = sympy.symbols('x_o y_o z_o')
x_f, y_f, z_f = sympy.symbols('x_f y_f z_f')
x_s, y_s, z_s = sympy.symbols('x_s y_s z_s')
t = sympy.symbols('t', nonnegative=True)

r, t_0, t_1, t_2, t_3 = sympy.symbols('r t_0 t_1 t_2 t_3')

d0, d1, d2, d3 = sympy.symbols('d d1 d2 d3')
x_p0, y_p0, z_p0 = sympy.symbols('x_p0 y_p0 z_p0')
x_p1, y_p1, z_p1 = sympy.symbols('x_p1 y_p1 z_p1')
x_p2, y_p2, z_p2 = sympy.symbols('x_p2 y_p2 z_p2')
x_p3, y_p3, z_p3 = sympy.symbols('x_p3 y_p3 z_p3')
x_sp0, y_sp0, z_sp0 = sympy.symbols('x_sp0 y_sp0 z_sp0')
x_sp1, y_sp1, z_sp1 = sympy.symbols('x_sp1 y_sp1 z_sp1')
x_sp2, y_sp2, z_sp2 = sympy.symbols('x_sp2 y_sp2 z_sp2')
x_sp3, y_sp3, z_sp3 = sympy.symbols('x_sp3 y_sp3 z_sp3')

# declare equations ------------------------------------

## object to cylinder projection
eq_line_FO_x = sympy.Eq(x_s, x_f + (x_o - x_f) * t)
eq_line_FO_y = sympy.Eq(y_s, y_f + (y_o - y_f) * t)
eq_line_FO_z = sympy.Eq(z_s, z_f + (z_o - z_f) * t)
eq_cylinder = sympy.Eq(x_s*x_s + y_s*y_s, r*r)

## cylinder to screen projection

# ----- Projector 0: left
eq_proj0_x = sympy.Eq(x_p0, -d0)
eq_proj0_y = sympy.Eq(y_p0, 0)
eq_proj0_z = sympy.Eq(z_p0, 0)
eq_line_SP0_x = sympy.Eq(x_sp0, x_s + (x_p0 - x_s) * t_0)
eq_line_SP0_y = sympy.Eq(y_sp0, y_s + (y_p0 - y_s) * t_0)
eq_line_SP0_z = sympy.Eq(z_sp0, z_s + (z_p0 - z_s) * t_0)
eq_screen_plane0 = sympy.Eq(x_sp0, -r)

# ----- Projector 1: top
eq_proj1_x = sympy.Eq(x_p1, 0)
eq_proj1_y = sympy.Eq(y_p1, d1)
eq_proj1_z = sympy.Eq(z_p1, 0)
eq_line_SP1_x = sympy.Eq(x_sp1, x_s + (x_p1 - x_s) * t_1)
eq_line_SP1_y = sympy.Eq(y_sp1, y_s + (y_p1 - y_s) * t_1)
eq_line_SP1_z = sympy.Eq(z_sp1, z_s + (z_p1 - z_s) * t_1)
eq_screen_plane1 = sympy.Eq(y_sp1, r)

# ----- Projector 2: right
eq_proj2_x = sympy.Eq(x_p2, d2)
eq_proj2_y = sympy.Eq(y_p2, 0)
eq_proj2_z = sympy.Eq(z_p2, 0)
eq_line_SP2_x = sympy.Eq(x_sp2, x_s + (x_p2 - x_s) * t_2)
eq_line_SP2_y = sympy.Eq(y_sp2, y_s + (y_p2 - y_s) * t_2)
eq_line_SP2_z = sympy.Eq(z_sp2, z_s + (z_p2 - z_s) * t_2)
eq_screen_plane2 = sympy.Eq(x_sp2, r)

# ----- Projector 3: bottom
eq_proj3_x = sympy.Eq(x_p3, 0)
eq_proj3_y = sympy.Eq(y_p3, -d3)
eq_proj3_z = sympy.Eq(z_p3, 0)
eq_line_SP3_x = sympy.Eq(x_sp3, x_s + (x_p3 - x_s) * t_3)
eq_line_SP3_y = sympy.Eq(y_sp3, y_s + (y_p3 - y_s) * t_3)
eq_line_SP3_z = sympy.Eq(z_sp3, z_s + (z_p3 - z_s) * t_3)
eq_screen_plane3 = sympy.Eq(y_sp3, -r)

# solve equations ------------------------------------

solutions = sympy.solve(
    [
        eq_line_FO_x,
        eq_line_FO_y,
        eq_line_FO_z,
        eq_cylinder,
        eq_proj0_x,
        eq_proj0_y,
        eq_proj0_z,
        eq_line_SP0_x,
        eq_line_SP0_y,
        eq_line_SP0_z,
        eq_screen_plane0,
        eq_line_SP1_x,
        eq_line_SP1_y,
        eq_line_SP1_z,
        eq_screen_plane1,
        eq_line_SP2_x,
        eq_line_SP2_y,
        eq_line_SP2_z,
        eq_screen_plane2,
        eq_line_SP3_x,
        eq_line_SP3_y,
        eq_line_SP3_z,
        eq_screen_plane3
    ], 
    [
      x_sp0, x_sp1, x_sp2, x_sp3,
      y_sp0, y_sp1, y_sp2, y_sp3,
      z_sp0, z_sp1, z_sp2, z_sp3,
      t_0, t_1, t_2, t_3,
      x_p0, y_p0, z_p0, 
      x_p1, y_p1, z_p1, 
      x_p2, y_p2, z_p2, 
      x_p3, y_p3, z_p3, 
      z_s, x_s, y_s, t
    ],
    dict=True
)

# TODO: additional constraints: 
# F has to be inside the cylinder
# F and O cannot be in the same location 
