from copy import copy
from datetime import timedelta
import random
from typing import Any, Optional, Generator

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from API.models import Candidat, Parcours, Recherche, Stage, Sujet

_OPT_CANDIDATS = "candidats"
_OPT_PARCOURS = "parcours"
_OPT_RECHERCHES = "recherches"
_OPT_STAGES = "stages"
_OPT_SUJETS = "sujets"

_RAND_SEED = 42


def _decompose_base_26(number: int) -> Generator[int, None, None]:
    # A=1, B=2, …, Z=25

    if number < 26:
        yield number
    else:
        number, cur_digit = divmod(number, 26)
        yield from _decompose_base_26(number)
        yield cur_digit


def _base10_to_base26_alpha(number: int) -> str:
    upper_a_code = ord("A")
    return "".join(chr(upper_a_code + digit) for digit in _decompose_base_26(number))


class Command(BaseCommand):
    help = "Populates the database with some random fixtures"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._candidats: list[Candidat] = []
        self._parcours: list[Parcours] = []
        self._stages: list[Stage] = []
        self._sujets: list[Sujet] = []

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            f"--{_OPT_CANDIDATS}",
            action="store",
            default=10,
            type=int,
            help="How many Candidats to create per Stage",
        )
        parser.add_argument(
            f"--{_OPT_PARCOURS}",
            action="store",
            default=3,
            type=int,
            help="How many Parcours to create",
        )
        parser.add_argument(
            f"--{_OPT_RECHERCHES}",
            action="store",
            default=50,
            type=int,
            help="How many Stage to create per Candidate",
        )
        parser.add_argument(
            f"--{_OPT_STAGES}",
            action="store",
            default=1,
            type=int,
            help="How many Stage to create",
        )
        parser.add_argument(
            f"--{_OPT_SUJETS}",
            action="store",
            default=50,
            type=int,
            help="How many Sujets to create per Parcours",
        )

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        random.seed(_RAND_SEED)

        self._create_stages(options[_OPT_STAGES])
        self._create_parcours(options[_OPT_PARCOURS])
        self._create_sujets(options[_OPT_SUJETS])
        self._create_candidats(options[_OPT_CANDIDATS])
        self._create_recherches(options[_OPT_RECHERCHES])

    def _create_stages(self, nb_stages: int) -> None:
        if nb_stages < 1:
            raise CommandError(f"{_OPT_STAGES} must be greater than 0")

        for id_stage in range(nb_stages):
            stage = Stage(nom=f"Stage {id_stage}", date=timezone.now())
            stage.save()
            self._stages.append(stage)

    def _create_parcours(self, nb_parcours: int) -> None:
        if nb_parcours < 1:
            raise CommandError(f"{_OPT_PARCOURS} must be greater than 0")

        for id_parcours in range(nb_parcours):
            parcours_code = _base10_to_base26_alpha(id_parcours)
            parcours = Parcours(nom=f"Parcours {parcours_code}", code=parcours_code)
            parcours.save()
            self._parcours.append(parcours)

    def _create_sujets(self, nb_sujets_per_parcours: int) -> None:
        if nb_sujets_per_parcours < 1:
            raise CommandError(f"{_OPT_SUJETS} must be greater than 0")

        for parcours in self._parcours:
            for id_sujet in range(nb_sujets_per_parcours):
                # TODO add link to cute cat pic as placeholder
                nom = f"{parcours.nom}: {id_sujet}"
                sujet = Sujet(
                    nom=nom,
                    parcours=parcours,
                    ordre=id_sujet,
                    explications=f"Explication du sujet '{nom}':\nTODO",
                    correction="La réponse était: 42",
                )
                sujet.save()
                self._sujets.append(sujet)

    def _create_candidats(self, nb_candidats_per_stage: int) -> None:
        if nb_candidats_per_stage < 1:
            raise CommandError(f"{_OPT_CANDIDATS} must be greater than 0")

        id_candidat = 0
        for stage in self._stages:
            for _ in range(nb_candidats_per_stage):
                candidat = Candidat(
                    prenom=f"Cand#{id_candidat}",
                    nom=f"Didat#{id_candidat}",
                    annee_bac=2042,
                    login=f"candidat{id_candidat}",
                )
                candidat.save()
                stage.candidats.add(candidat)
                stage.save()

                self._candidats.append(candidat)
                id_candidat += 1

    def _create_recherches(self, nb_recherches_per_candidat: int) -> None:
        for candidat in self._candidats:
            sujets = copy(self._sujets)
            random.shuffle(sujets)
            recherches = []
            for sujet in sujets[:nb_recherches_per_candidat]:
                now = timezone.now()
                validated = bool(random.randint(0, 1))
                validated_at = now
                started = validated or bool(random.randint(0, 1))
                started_at = now - timedelta(minutes=random.randint(0, 2 * 60))
                read = started or bool(random.randint(0, 1))
                read_at = started_at - timedelta(minutes=random.randint(0, 10))

                recherche = Recherche(
                    candidat=candidat,
                    sujet=sujet,
                    premiere_lecture=read_at if read else None,
                    faux_debut=started_at if started else None,
                    demarrage_officiel=started_at if started else None,
                    validation=validated_at if validated else None,
                )
                recherche.save()
                recherches.append(recherche)
            if len(recherches) > 0:
                candidat.sujet = recherches[0].sujet
                candidat.save()
