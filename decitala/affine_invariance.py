
def affine_coordinates(v, a=(1, -2), b=(2, -1), c=(3, 2)):
    """
    Given 3 non-colinear basis vectors, a, b, & c, returns the affine invariant
    coordinates of vector v. Currently restricted to R2. 

    Supposedly, the affine coordinates of v are invariant if an affine transformation T is applied. 
    """
    denominator = ((a[0]-c[0]) * (b[1] - c[1])) - ((b[0] - c[0]) * (a[1] - c[1]))
    x_coord_numerator = ((v[0] - c[0]) * (b[1] - c[1])) - ((b[0] - c[0]) * (v[1] - c[1]))
    y_coord_numerator = ((a[0] - c[0]) * (v[1] - c[1])) - ((v[0] - c[0]) * (a[1] - c[1]))

    return (x_coord_numerator / denominator, y_coord_numerator / denominator)

print(affine_coordinates(v=(2.25, 2.25)))

