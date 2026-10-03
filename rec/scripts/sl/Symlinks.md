# Enlaces simbólicos (Symlinks)


# Comentarios adicionales del desarrollador


## Comandos básicos

```bash
# Crear absoluto
ln -s <origen> <simbólico>

# Crear relativo
ln -sr <origen> <simbólico>

# Borrar (verifica que es simbólico antes)
[ -L <simbólico> ] && rm <simbólico>

# Convertir todos los absolutos a relativos en el proyecto
find . -type l | while read sl; do
    target=$(readlink "$sl")
    if [[ "$target" == /* ]]; then ln -srf "$target" "$sl"; fi
done
```

---

Simlink                     Path real
