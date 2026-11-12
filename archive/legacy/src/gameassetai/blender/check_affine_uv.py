"""Pure development guard: one affine UV map over coplanar source corners."""
import math


def _affine_tolerances(tolerance=None, geometry_tolerance=None, uv_tolerance=None):
    if tolerance is not None:
        if geometry_tolerance is not None or uv_tolerance is not None:
            raise ValueError("Do not mix legacy and separate tolerances")
        geometry_tolerance=uv_tolerance=tolerance
    for value in (geometry_tolerance,uv_tolerance):
        if type(value) not in {int,float} or not math.isfinite(value) or value<=0:
            raise ValueError("Explicit finite positive geometry and UV tolerances required")
    return geometry_tolerance,uv_tolerance


def check_affine_uv(corners, tolerance=None, *, geometry_tolerance=None, uv_tolerance=None):
    """Absolute local-xyz and UV bounds; legacy tolerance sets both explicitly."""
    report={"status":"error","reason":None,"mutation_authorized":False}
    try:
        geometry_tolerance,uv_tolerance=_affine_tolerances(tolerance,geometry_tolerance,uv_tolerance)
        if not isinstance(corners,(list,tuple)) or len(corners)<3:
            raise ValueError("At least three corners required")
        for corner in corners:
            if not isinstance(corner,(list,tuple)) or len(corner)!=2:
                raise ValueError("Expected xyz/uv corner pairs")
            xyz,uv=corner
            if len(xyz)!=3 or len(uv)!=2 or any(type(x) not in {int,float} or
                    not math.isfinite(x) for x in (*xyz,*uv)):
                raise ValueError("Expected finite xyz and uv values")
        origin,base_uv=corners[0]
        sub=lambda a,b: tuple(x-y for x,y in zip(a,b))
        dot=lambda a,b: sum(x*y for x,y in zip(a,b))
        basis=None
        for i in range(1,len(corners)):
            for j in range(i+1,len(corners)):
                a,b=sub(corners[i][0],origin),sub(corners[j][0],origin)
                aa,ab,bb=dot(a,a),dot(a,b),dot(b,b)
                determinant=aa*bb-ab*ab
                if not all(math.isfinite(v) for v in (aa,ab,bb,determinant)):
                    raise ValueError("Basis arithmetic is not finite")
                if determinant>geometry_tolerance**4:
                    basis=(a,b,aa,ab,bb,determinant,
                           sub(corners[i][1],base_uv),sub(corners[j][1],base_uv))
                    break
            if basis:
                break
        if basis is None:
            report.update(status="blocked",reason="degenerate_basis")
            return report
        a,b,aa,ab,bb,determinant,du,dv=basis
        for xyz,uv in corners:
            delta=sub(xyz,origin)
            da,db=dot(delta,a),dot(delta,b)
            s,t=(da*bb-db*ab)/determinant,(db*aa-da*ab)/determinant
            residual=[delta[k]-s*a[k]-t*b[k] for k in range(3)]
            uv_residual=[uv[k]-base_uv[k]-s*du[k]-t*dv[k] for k in range(2)]
            if not all(math.isfinite(v) for v in (s,t,*residual,*uv_residual)):
                raise ValueError("Mapping arithmetic is not finite")
            if any(abs(v)>geometry_tolerance for v in residual):
                report.update(status="blocked",reason="noncoplanar")
                return report
            if any(abs(v)>uv_tolerance for v in uv_residual):
                report.update(status="blocked",reason="nonaffine_or_discontinuous_uv")
                return report
        report.update(status="affine",reason="within_explicit_tolerance")
    except (ValueError,TypeError,OverflowError) as exc:
        report["reason"]=str(exc)
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
