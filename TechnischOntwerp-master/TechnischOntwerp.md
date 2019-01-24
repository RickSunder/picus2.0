# Technisch Ontwerp
## Controllers
1. login.html (POST)
* De gebruiker moet kunnen inloggen om bij de functie in een besloten groep zitten te komen of om een event aan te maken.
2. register.html (POST)
* De gebruiker moet zich kunnen registreren, waarbij checks zijn of de gebruikersnaam al bestaat, het wachtwoord overeenkomt en of het een geldig e-mailadres is.
3. groupfeed.html (POST)(Homepage)
* Homepage als je ingelogd bent. Hierop kan je je besloten groepen zien en daar naartoe gaan.
4. makegroup.html / addgroupmember.html (POST (idk))
* Hierbij moet je een groep kunnen aanmaken en gebruikers kunnen toevoegen
5. groupview.html(https://PicUs.com/groups/desbetreffende_groep)(POST)
* Dit is de homepage van een groep waarbij je allemaal foto's kunt zien, kunt liken en disliken. Daarnaast kan je een groep verlaten en mensen toevoegen aan de groep.
6. settings.html(POST)
* Link naar je wachtwoord veranderen en je username veranderen. Daarnaast kun je meer over onze website lezen en uitloggen.
7. password.html(POST)
* Hierbij kan je je wachtwoord veranderen.
8. aboutUs.html(GET)
* Hier lees je meer informatie over onze website.
9. makeevent.html(POST)
* Hierbij kan je als je ingelogd bent een event aanmaken.
10. index.html(GET)
* De index is de homepage van onze website als je nog niet bent ingelogd. Hierbij wordt je doorverwezen naar de registratie.
11. event.html(POST/GET)
* Homepage van de event waarbij niet-gebruikers van onze website alsnog de foto's van het event kunnen zien.
12. addmembers.html(POST)
* Functie om gebruikers toe te voegen aan een groep.
13. search.html(GET/POST)
* Hierbij kun je zoeken naar een evenement.

## Views:
![schets](doc/IMG_2173.jpg)
![schets](doc/IMG_2174.jpg)
![schets](doc/IMG_2175.jpg)
![schets](doc/IMG_2176.jpg)
![schets](doc/IMG_2177.jpg)

## Models:
* Het opzoeken van een user
* Het opzoeken van een groep
* De foto van een groep geplaatst door iemand opzoeken
* Login vereist
* Het aantal likes ophalen
* De foto's ophalen
* De profielfoto ophalen

## Framework:
* [Bootstrap navigatie bar](https://bootsnipp.com/snippets/Vm7d)
* [Eventueel bootstrap voor het liken van foto’s](https://bootsnipp.com/snippets/featured/modal-lightbox-with-likedislike)

## Eventuele extra links:
* gebruikersnaam.html(POST)
* mijn-fotos.html(POST)
* vrienden.html(POST)
