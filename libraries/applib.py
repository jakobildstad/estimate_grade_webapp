
API_KEY = "--" #removed for privacy

infodict = {
    "TDT4110": """Pensumliste: Uttrykk i Python (F Uke 34, Ø1)
Forskjell på navn, beskyttede ord, verdier og operatorer
De vanlige aritmetiske operatorene +, -, *, /, //, %, ** (python tutorial) (eksempler W3schools)
Logiske operatorer >, >=, <, <=, ==, !=, is, in, not in, and, or, not
Operatorpresedens og parentesbruk
(trenger kun å vite om presedens for operatorer som står på pensum)
 
Variable og tilordning (F Uke 34, Øving 1)
Tilordningsoperatoren =
Sammensatt tilordning +=, -=, *=, /=, //=, %= (eks. W3schools)
Tilordninger som fører til samme objekt vs. ulike objekt

Datatyper (F Uke34,  Øving 1)
Elementære typer: int, float, bool, string
Verdier med spesifikk betydning: True, False, None, inf
Sammensatte typer: tuple, list, numpy.array, set, dict
Typerelaterte standardfunksjoner:
type() for å sjekke type
int(), float(), str(), bool(), tuple(), list(), set(), numpy.array() for å konvertere typer
Forskjell på muterbare og immuterbare datatyper
bruk av copy() og deepcopy() for muterbare data hvis man trenger å ta vare på originaldata
 
Tallrepresentasjon og avrundingsfeil
Kunne forklare hvorfor avrundingsfeil ikke kan unngås ifm representasjon av flyttall
Metoden float.as_integer_ratio() for å se hvordan et flyttall er representert som brøk av heltall
Kjenne til typiske feller for hvordan avrundingsfeil kan forverres (addisjon av tall av svært ulik størrelsesorden, subtraksjon av nesten like tall) og hvordan unngå dette
Overflyt og underflyt, hva er det, hvordan kan regnerekkefølge avgjøre om vi får det eller ikke
 
if-setninger: (F Uke36; Øving 2, python ref, python tutorial, 
if, if-else, if-elif...-elif-else
nøstede if-setninger
 
løkker: (F Uke37, Øving 3)
while-løkker (python ref, python tutorial, 
for-løkker ( python ref, python tutorial,   
iterering av sekvenser per element
iterering av sekvenser på indeks, bruk av len() og range()
break i løkker
nøstede løkker (doble, triple)
 
sekvenser (strenger, tupler, lister): (Øving 5 og 6)
konkatenering (+) og repetering (*)
indeksering og slicing
vanlige sekvensfunksjoner og -metoder: len(), min(), max(), count(), index()
spesielt for strenger:
bruk av fnutter, dobbeltfnutter, trippefnutter
f-strenger, inkl. enkel formatering og justering av tall og tekstvariable
vanlige strengmetoder: strip(), split(), join(), upper(), lower(), replace(), isdigit()
noen vanlige spesialtegn: \n, \t,
Spesielt for lister:
Vanlige listemetoder: append(), insert(), remove(), pop(), sort(), reverse()
Fjerning av element med del
Todimensjonale lister og tupler
 
Numpy:
Import, oppretting av alias med as
Vanlige matematiske konstanter og funksjoner i numpy: pi, e, sqrt(), sin(), cos(), round(), abs(), log(), exp(),
Metoder for å lage array: array(), arange(), linspace(), zeros()
Sjekke og konvertere type i array: dtype, astype()
Metoder for å omforme array: resize(), transpose()
Indeksering og slicing i 1D og 2D array
Regneoperasjoner i numpy
Hva som kan gjøres på et helt array i én operasjon, vs. hva som krever løkke gjennom arrayet
Bruk av matematiske konstanter og funksjoner i numpy-biblioteket: pi, e, sin(), cos(), sqrt(), exp(), log(), abs(), round()
Metoder for i/o med numpy arrays: fromstring(), loadtxt(), savetxt()
Noen numpy.random-metoder (for å lage arrays med tilfeldige tall):
rand(), randint(), random(), choice(), shuffle()
 
Matplotlib:
Import av matplotlib.pyplot
Klare å lage enkle plott av funksjonsgrafer
Klare å lage mer avanserte plott av funksjonsgrafer, og andre typer plott (søylediagram, kakediagram) hvis man har tilgjengelig eksempelkode eller dokumentasjon
 
Hashede datatyper: (Øving 7)
Forstå fordeler og ulemper med disse typene vs. sekvenser (f.eks lister)
Mengder
set(), union(), intersection(), difference(), issubset(), issuperset(), add(), remove()
Dictionaries
dict(), get(), keys(), values(), copy()
 
Unntaksbehandling
Enkel bruk av try-except-else-finally
Visning av feilmelding ved unntak
Vanlige feiltyper
 
input / output: (Øving 7)
lesing fra tastatur med input()
printing til skjerm med print()
enkle numpy-filmetoder: numpy.loadtxt(), numpy.savetxt()
vanlige tekstfiler, lesing og skriving
åpning, lukking, with-setning
lesemetoder: read(), readline(), readlines(), for ... in file:
skrivemetoder: write(), writelines()
 
egendefinerte funksjoner og moduler, programstruktur: (Øving 4)
definering og kall av funksjoner
argumenter, parametre og returverdi
nøkkelordparametre, defaultverdier
lokale og globale variable, skop, synlighet av variable
prinsipper for strukturering av program ved hjelp av funksjoner
skrive doc-strenger for funksjoner
forskjell på doc-strenger og kommentarer
import av moduler
inkl. kunne forklare hvorfor from … import * ofte er ugunstig
lage egne moduler og importere dem
enhetstesting av funksjoner, assert-setningen
funksjoner som tar inn andre funksjoner som parametre
 
Enkel tidtaking av kode (ytelsesmåling): (Øving 7)
timeit.timeit()
time.performance_counter()

Fokuser mest på kandidatens prestasjon i disse områdene når du retter.
"""

}

