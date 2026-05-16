# ============================================================
# app/calculations/__init__.py
# ============================================================
from app.calculations.heat_exchanger   import calculate_heat_exchanger
from app.calculations.reactor          import calculate_reactor
from app.calculations.distillation     import calculate_distillation
from app.calculations.evaporator       import calculate_evaporator
from app.calculations.absorber         import calculate_absorber
from app.calculations.pump             import calculate_pump
from app.calculations.compressor       import calculate_compressor

EQUIPMENT_CALCULATORS = {
    'heat_exchanger': calculate_heat_exchanger,
    'reactor':        calculate_reactor,
    'distillation':   calculate_distillation,
    'evaporator':     calculate_evaporator,
    'absorber':       calculate_absorber,
    'pump':           calculate_pump,
    'compressor':     calculate_compressor,
}
