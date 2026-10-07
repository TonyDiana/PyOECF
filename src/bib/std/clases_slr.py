# -*- coding: utf-8 *-*
"""
    :Propósito: Manejadores de clases
    :Autor:     Tony Diana
    :Versión:   26.09.09

    Métodos mágicos que obligan a usar una metaclase.

Un mixin normal solo define comportamiento para las INSTANCIAS. Cuando
se necesita interceptar una operación sobre la CLASE misma (no sobre un
objeto creado a partir de ella), el método mágico debe vivir en la
metaclase — porque Python busca los métodos mágicos de un objeto en
``type(objeto)``, y el tipo de una clase es su metaclase.

+---------------------------+-------------------------------------------+
| Método mágico             | Qué controla sobre la clase                |
+===========================+=============================================+
| ``__setattr__``           | ``Clase.attr = valor``                     |
| ``__delattr__``           | ``del Clase.attr``                         |
| ``__getattr__``           | ``Clase.attr`` (lectura, si no existe)     |
| ``__getattribute__``      | ``Clase.attr`` (lectura, siempre)          |
| ``__call__``              | ``Clase(...)`` — creación de instancias    |
| ``__iter__``              | ``for x in Clase:``                        |
| ``__len__``               | ``len(Clase)``                             |
| ``__contains__``          | ``x in Clase``                             |
| ``__repr__`` / ``__str__``| ``repr(Clase)`` / ``str(Clase)``           |
| ``__instancecheck__``     | ``isinstance(obj, Clase)``                 |
| ``__subclasscheck__``     | ``issubclass(Sub, Clase)``                 |
+---------------------------+-------------------------------------------+

.. note::
    ``Enum`` resuelve ``__iter__`` y ``__contains__`` en su propia
    metaclase (``EnumMeta``/``EnumType``) — por eso ``for m in cls`` y
    ``"algo" in cls`` funcionan sobre la clase, no solo sobre instancias.
"""

# cSpell:ignore unico

__all__ = ["noInst", "InmutableMeta", "classproperty", "classDict", "dictEnum",
           "EnumMutable", "SingleRun", "TDSingleton"]

# --- Librería estándar Python
import socket


# --- Tipado
from typing import Any, Callable, Generic, Optional, TypeVar
_T = TypeVar("_T")


#
class noInst(object):
    """ Clase que impide la instancia. Pensada para heredar. """

    # --- Evitar que se instancie la clase
    def __new__(cls, *args, **kwargs):
        raise TypeError(f"La clase {cls.__name__} no puede ser instanciada")


#
class classproperty(Generic[_T]):
    """
    Decorador que convierte un método en una propiedad de sólo lectura
    accesible sin instanciar la clase (``Clase.algo`` en vez de
    ``Clase().algo``).

    USO:
        @classproperty
        def algo(cls) -> int:
            return cls._algo
    """

    __slots__ = ["fget"]

    def __init__(self, fget: Callable[[Any], _T]) -> None:
        self.fget = fget

    @property
    def __doc__(self) -> str | None:
        """ Documentación del método decorado, para Sphinx y help(). """
        return self.fget.__doc__

    def __get__(self, instance: Any, owner: Optional[type] = None) -> _T:
        cls = owner if owner is not None else type(instance)
        return self.fget(cls)


#
class InmutableMeta(type):
    """
        Metaclase que impide añadir atributos nuevos a la clase.
        Si el atributo de clase ``INMUTABLE`` vale ``True``, además impide
        modificar cualquier atributo ya existente.

        USO: ``class MiClase(metaclass=InmutableMeta):``
    """

    # --- Anotación vacía, solo para que Pylance conozca el atributo;
    #     el valor real lo asigna la línea de abajo, dinámicamente
    # --- Switch de mutabilidad
    __name_inmutable: str = "INMUTABLE"
    locals()[__name_inmutable] = False

    #
    def __setattr__(cls, nombre, valor):

        # --- Si la clase está marcada como inmutable, bloquear cualquier
        #     cambio, salvo el propio interruptor INMUTABLE
        if ((nombre != cls.__name_inmutable) and
                getattr(cls, cls.__name_inmutable)):
            raise AttributeError(
                f"La clase '{cls.__name__}' es inmutable, "
                f"no se puede modificar '{nombre}'"
            )

        if not hasattr(cls, nombre):
            raise AttributeError(
                f"No se puede añadir el atributo nuevo '{nombre}' "
                f"a la clase '{cls.__name__}'"
            )

        # --- Escribir en la clase que YA POSEE el atributo (la propia
        #     si ya lo tiene como suyo, si no el primer ancestro del
        #     MRO que lo define) — evita que una subclase tape en
        #     silencio el valor de la clase base en vez de compartirlo
        #     con ella (y con el resto de subclases hermanas)
        destino = next(
            (c for c in cls.__mro__ if nombre in c.__dict__), cls
        )
        type.__setattr__(destino, nombre, valor)


#
class classDict(object):
    """
        Clase que, al ser heredada, permite que todos los atributos y
        propiedades de una clase o instancia se devuelvan como un
        diccionario o como una lista de sus claves.

        Contempla dos escenarios distintos porque no existe en Python un
        único mecanismo que resuelva atributos calculados (``@property``,
        ``classproperty``) por igual desde la clase y desde la instancia:

        - ``dictClass()`` / ``KeysClass()``: para invocar SIN instanciar,
          típicamente sobre clases marcadas como ``noInst``. Solo ve
          atributos y ``classproperty`` de la propia clase.

        - ``dictInstancia()`` / ``KeysInstancia()``: para invocar sobre una
          instancia real. Ve tanto lo heredado de la clase como lo propio
          de esa instancia, incluidas ``@property`` normales.

        Cada atributo/propiedad se resuelve siempre con ``getattr`` (nunca
        con ``vars``), para que cualquier ``classproperty``/``@property``
        se calcule de verdad, en vez de devolver el descriptor sin resolver.

        Los cuatro métodos que expone esta clase son siempre invocables con
        ``()``, nunca ``@property`` — así ``callable()`` los filtra a todos
        por igual, sin necesitar ninguna lista de exclusión explícita.
    """

    #
    # --- Diccionarios de atributos y propiedades
    #

    @classmethod
    def dictClass(cls) -> dict:
        return cls.__dict(cls)

    def dictInstancia(self) -> dict:
        return self.__class__.__dict(self)

    #
    # --- Lista de key's o nombres de atributos y propiedades
    #

    @classmethod
    def KeysClass(cls) -> list:
        return cls.__keys(cls)

    def KeysInstancia(self) -> list:
        return self.__class__.__keys(self)

    #
    # --- Constructores privados
    #

    @staticmethod
    def __dict(ente) -> dict:
        resultado = {}
        for nombre in dir(ente):
            if nombre.startswith("_"):
                continue
            valor = getattr(ente, nombre)
            if callable(valor):
                continue
            resultado[nombre] = valor
        return resultado

    @staticmethod
    def __keys(ente) -> list:
        resultado = []
        for nombre in dir(ente):
            if nombre.startswith("_"):
                continue
            valor = getattr(ente, nombre)
            if callable(valor):
                continue
            resultado.append(nombre)
        return resultado


#
class dictEnum(object):
    """
    Mixin para Enum: expone dictClass() para inyectar la enumeración
    como diccionario simple {nombre: valor} — por ejemplo, hacia Jinja
    o hacia JS con | tojson.

    A diferencia de classDict, no usa dir()/getattr() genérico: itera
    los miembros reales de la enumeración y extrae su .value, porque
    getattr() sobre un Enum siempre devuelve el objeto miembro completo,
    nunca su valor.

    USO: class APP(dictEnum, Enum):
    """

    @classmethod
    def dictClass(cls) -> dict:
        return {m.name: m.value for m in cls}                   # type: ignore


#
class EnumMutable(noInst, classDict, metaclass=InmutableMeta):
    """ Convierte cualquier clase en un enum mutable.

    USO: class APP(EnumMutable):
    """
    pass


#
class SingleRun(object):
    """
    Control de instancia única multiplataforma.
    Utiliza sockets TCP en un puerto efímero para asegurar exclusividad
    de forma atómica en cualquier Sistema Operativo.
    """

    __slots__ = ["__socket", "__unico"]

    def __init__(self, ente: str, port: int = 47200) -> None:
        # Usamos un socket TCP en localhost para compatibilidad total
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__unico = True

        try:
            # Intentamos hacer bind a una dirección local.
            # Si el puerto está ocupado, otra instancia ya está corriendo.
            self.__socket.bind(("127.0.0.1", port))
            self.__socket.listen(1)

        except socket.error:
            self.__unico = False
            self.__socket.close()
            self.__socket = None

    #
    @property
    def getUnico(self) -> bool:
        """ Saber si es único u otro ente igual ya existe. """
        return self.__unico

    #
    def release(self):
        """ Liberar el ente del único. """
        if self.__unico and self.__socket is not None:
            try:
                self.__socket.close()
            except Exception:
                pass
            finally:
                self.__socket = None
                self.__unico = False

    #
    def __enter__(self):
        return self

    #
    def __exit__(self, exc_type, exc, tb):
        self.release()


#
class TDSingleton(object):
    """ Super sencillo Singleton. Sólo para propósitos muy sencillos. """

    def __new__(cls):
        if not hasattr(cls, "_instancia"):
            cls._instancia = super().__new__(cls)
        return cls._instancia
