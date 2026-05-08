# Material database — short version

Most important classic `.zcode` material IDs used by the converter:

```text
Z-ABS legacy        0x00
Z-ULTRAT            0x01
Z-GLASS             0x02
Z-HIPS              0x03
Z-PCABS             0x04
Z-PETG              0x05
Z-ULTRAT Plus       0x06
Z-SUPPORT           0x07
Z-ESD               0x08
Z-PHA               0x09
Z-PLA               0x0A
Z-PLA Pro           0x0B
Z-ASA Pro           0x0C
Z-SUPPORT Plus      0x0D
Z-SEMIFLEX          0x0E
Z-FLEX              0x0F
Z-NYLON             0x10
Z-SUPPORT Premium   0x11
Z-PEEK              0x12
Z-SUPPORT ATP       0x13 experimental for Inventure classic
BASF Ultrafuse BVOH 0x17
PETG-based external 0x83
```

The safest mapping source is a Filament Advanced comment:

```gcode
;ZORTRAX_FILAMENT_PROFILE canonical=Z-PLA zcode=0x0A role=model support_role=0 experimental=0
```

Do not put real `M104/M109/G1/T0/T1` commands in Filament Advanced; use diagnostic comments only.
