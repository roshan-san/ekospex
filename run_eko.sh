#!/bin/bash
echo "Starting run_eko.sh" >> /tmp/ekospex_debug.log
# Attempt to activate the virtual environment (though we might not rely on PATH)
source venv/bin/activate 2>> /tmp/ekospex_debug.log || echo "Warning: Venv activation failed (may be okay)" >> /tmp/ekospex_debug.log
echo "Virtual environment activation attempted." >> /tmp/ekospex_debug.log
which python >> /tmp/ekospex_debug.log
/home/admin/ekospex/venv/bin/python eko.py >> /tmp/ekospex_debug.log 2>&1
echo "run_eko.sh finished" >> /tmp/ekospex_debug.log
