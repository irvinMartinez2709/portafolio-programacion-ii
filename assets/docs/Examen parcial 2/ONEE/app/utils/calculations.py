from decimal import Decimal


def calcular_delivery(monto_flete: float, porcentaje_comision: float = 60.0, propina: float = 0.0):
    """
    Calcula la distribución del flete entre repartidor y empresa.
    
    Ejemplo:
        flete = 3.50, comisión 60%
        repartidor = 2.10 + propina
        empresa    = 1.40
    """
    try:
        flete = Decimal(str(monto_flete))
        pct   = Decimal(str(porcentaje_comision)) / Decimal('100')
        tip   = Decimal(str(propina))

        comision_repartidor      = (flete * pct).quantize(Decimal('0.01'))
        ganancia_empresa_delivery = (flete - comision_repartidor).quantize(Decimal('0.01'))
        ganancia_total_repartidor = (comision_repartidor + tip).quantize(Decimal('0.01'))

        return {
            'monto_flete':              float(flete),
            'porcentaje_comision':       float(porcentaje_comision),
            'comision_repartidor':       float(comision_repartidor),
            'ganancia_empresa_delivery': float(ganancia_empresa_delivery),
            'propina':                   float(tip),
            'ganancia_total_repartidor': float(ganancia_total_repartidor),
        }
    except Exception as e:
        return {'error': str(e)}


def calcular_total_pedido(subtotal: float, monto_delivery: float = 0.0,
                          descuento: float = 0.0, impuesto_pct: float = 0.0):
    """
    Calcula el total de un pedido aplicando delivery, descuento e impuesto (ITBMS).
    """
    try:
        sub  = Decimal(str(subtotal))
        del_ = Decimal(str(monto_delivery))
        desc = Decimal(str(descuento))
        pct  = Decimal(str(impuesto_pct)) / Decimal('100')

        base       = sub + del_ - desc
        impuesto   = (base * pct).quantize(Decimal('0.01'))
        total      = (base + impuesto).quantize(Decimal('0.01'))

        return {
            'subtotal':         float(sub),
            'monto_delivery':   float(del_),
            'descuento':        float(desc),
            'impuesto':         float(impuesto),
            'total':            float(total),
        }
    except Exception as e:
        return {'error': str(e)}
