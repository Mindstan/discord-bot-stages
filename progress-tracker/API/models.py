from django.db import models


class Parcours(models.Model):
   nom = models.CharField(max_length=256)
   code = models.CharField(max_length=256)
   
   def __str__(self):
      return self.nom
      

class Sujet(models.Model):
   nom = models.CharField(max_length=256)
   parcours = models.ForeignKey(Parcours, null=True, blank=True, on_delete=models.SET_NULL)
   ordre = models.IntegerField()
   lien = models.CharField(max_length=1024, null=True, blank=True)
   correction = models.CharField(max_length=1024, null=True, blank=True)
   explications = models.TextField(null=True, blank=True)
   
   def __str__(self):
      return self.nom

class Candidat(models.Model):
   prenom = models.CharField(max_length=256, null=True, blank=True)
   nom = models.CharField(max_length=256, null=True, blank=True)
   annee_bac = models.IntegerField(null=True, blank=True)
   login = models.CharField(max_length=256, null=True, blank=True)
   discord_name = models.CharField(max_length=256, null=True, blank=True)
   sujet = models.ForeignKey(Sujet, null=True, blank=True, on_delete=models.SET_NULL)
   
   def __str__(self):
      return self.prenom + " " + self.nom + " (" + self.login + ")"

class Recherche(models.Model):
   candidat = models.ForeignKey(Candidat, null=True, blank=True, on_delete=models.CASCADE)
   sujet = models.ForeignKey(Sujet, null=True, blank=True, on_delete=models.SET_NULL)
   premiere_lecture = models.DateTimeField(null=True, blank=True)
   demarrage_officiel = models.DateTimeField(null=True, blank=True)
   validation = models.DateTimeField(null=True, blank=True)
   
   debut_pause = models.DateTimeField(null=True, blank=True)
   faux_debut = models.DateTimeField(null=True, blank=True)
   
   commentaires = models.TextField(null=True, blank=True)
   
   def __str__(self):
      return str(self.candidat) + " / " + str(self.sujet)

class Stage(models.Model):
   nom = models.CharField(max_length=256)
   date = models.DateField()
   statut = models.CharField(max_length=256)
   candidats = models.ManyToManyField(Candidat)
   
   def __str__(self):
      return self.nom

