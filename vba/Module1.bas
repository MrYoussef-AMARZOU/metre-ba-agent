Attribute VB_Name = "Module1"
Option Explicit

'============================================================
' Module1 — Métré BA : navigation, audit, réinitialisation
'------------------------------------------------------------
' INSTALLATION :
'   1. Ouvrir le classeur .xlsx généré par generators/modele_metre.py
'   2. Onglet Développeur > Visual Basic > Fichier > Importer un fichier
'   3. Sélectionner Module1.bas
'   4. Fichier > Enregistrer sous > Classeur .xlsm
'
' LIGNES DE RÉFÉRENCE (à ajuster si la structure du modèle change) :
'   01_Detail_Quantitatif : en-têtes ligne 6, blocs lignes 7+, J=Qté,
'                           K=Totaux, ligne TOTAL GÉNÉRAL en bas
'   02_Armatures           : en-têtes ligne 3, données lignes 4+, K = T6,
'                           ligne "POIDS TOTAL DES ACIERS (KG)" en K
'============================================================

'------------------------------------------------------------
' 1. NAVIGATION FLUIDE (à lier aux boutons de chaque feuille)
'------------------------------------------------------------
Public Sub NaviguerVers(nomFeuille As String)
    On Error GoTo ErrHandler
    ThisWorkbook.Worksheets(nomFeuille).Activate
    Range("A1").Select
    Exit Sub
ErrHandler:
    MsgBox "Feuille introuvable : " & nomFeuille, _
           vbExclamation, "PlanBA — Navigation"
End Sub

Public Sub AllerDetail()
    NaviguerVers "01_Detail_Quantitatif"
End Sub

Public Sub AllerArmatures()
    NaviguerVers "02_Armatures"
End Sub

Public Sub AllerSynthese()
    NaviguerVers "03_Attachement_Ferraillage"
End Sub

Public Sub AllerBordereau()
    NaviguerVers "04_GO_Attachement"
End Sub

'------------------------------------------------------------
' 2. AUDIT MÉTRÉ — équilibre acier + contrôle des dimensions
'------------------------------------------------------------
Public Sub VerifierCoherenceMetre()
    Dim ws1 As Worksheet, ws2 As Worksheet, ws4 As Worksheet
    Dim totalBeton As Double, totalAcier As Double
    Dim acierBordereau As Double, ecartAcier As Double
    Dim erreurs As String, nbErreurs As Long
    Dim r As Long, c As Long, v As Variant

    On Error GoTo ErrHandler
    Set ws1 = ThisWorkbook.Worksheets("01_Detail_Quantitatif")
    Set ws2 = ThisWorkbook.Worksheets("02_Armatures")
    Set ws4 = ThisWorkbook.Worksheets("04_GO_Attachement")

    '--- Totaux : béton (colonne K, dernière ligne non vide) ---
    totalBeton = DerniereValeurNumerique(ws1, 11)

    '--- Totaux : acier feuille 2 (ligne POIDS TOTAL DES ACIERS, col K) ---
    totalAcier = ValeurLigneLibelle(ws2, "POIDS TOTAL DES ACIERS (KG)", 11)

    '--- Acier rappelé au bordereau (ligne prix 4, col E) ---
    acierBordereau = ValeurLignePrix(ws4, 4, 5)

    '--- Équilibre acier (tolérance 1 kg) ---
    ecartAcier = Abs(totalAcier - acierBordereau)

    '--- Contrôle des dimensions saisies (nombres >= 0, pas de texte) ---
    erreurs = ""
    nbErreurs = 0
    ' Feuille 1 : F, G, H, I (lignes 7 à 60)
    For r = 7 To 60
        If Application.CountA(ws1.Range("B" & r & ":I" & r)) = 0 Then GoTo SuiteS1
        For c = 6 To 9
            v = ws1.Cells(r, c).Value
            If Not IsEmpty(v) Then
                If Not IsNumeric(v) Then
                    nbErreurs = nbErreurs + 1
                    erreurs = erreurs & "• 01_Detail ligne " & r & " col " & _
                              Chr(64 + c) & " : texte '" & v & "'" & vbCrLf
                ElseIf v < 0 Then
                    nbErreurs = nbErreurs + 1
                    erreurs = erreurs & "• 01_Detail ligne " & r & " col " & _
                              Chr(64 + c) & " : valeur négative" & vbCrLf
                End If
            End If
        Next c
SuiteS1:
    Next r
    ' Feuille 2 : D à J (lignes 4 à 40)
    For r = 4 To 40
        If Application.CountA(ws2.Range("A" & r & ":J" & r)) = 0 Then GoTo SuiteS2
        For c = 4 To 10
            v = ws2.Cells(r, c).Value
            If Not IsEmpty(v) Then
                If Not IsNumeric(v) Then
                    nbErreurs = nbErreurs + 1
                    erreurs = erreurs & "• 02_Armatures ligne " & r & " col " & _
                              Chr(64 + c) & " : texte '" & v & "'" & vbCrLf
                ElseIf v < 0 Then
                    nbErreurs = nbErreurs + 1
                    erreurs = erreurs & "• 02_Armatures ligne " & r & " col " & _
                              Chr(64 + c) & " : valeur négative" & vbCrLf
                End If
            End If
        Next c
SuiteS2:
    Next r

    '--- Bilan ---
    Dim statut As String
    If ecartAcier <= 1 And nbErreurs = 0 Then
        statut = "✅ ÉQUILIBRÉ — aucun écart détecté."
    Else
        statut = "⚠ À VÉRIFIER — voir détails ci-dessous."
    End If

    Dim msg As String
    msg = "AUDIT DU MÉTRÉ GROS ŒUVRE" & vbCrLf & vbCrLf & _
          "Total Béton (m³) ............ : " & Format(totalBeton, "#,##0.00") & vbCrLf & _
          "Total Acier Feuille 2 (kg) .. : " & Format(totalAcier, "#,##0") & vbCrLf & _
          "Acier Bordereau (kg) ........ : " & Format(acierBordereau, "#,##0") & vbCrLf & _
          "Écart acier (kg) ............ : " & Format(ecartAcier, "#,##0") & vbCrLf & _
          "Anomalies dimensions ....... : " & nbErreurs & vbCrLf & vbCrLf & _
          statut
    If nbErreurs > 0 Then
        msg = msg & vbCrLf & vbCrLf & Left(erreurs, 1500)
    End If
    MsgBox msg, IIf(ecartAcier <= 1 And nbErreurs = 0, vbInformation, vbExclamation), _
           "PlanBA — Audit Métré"
    Exit Sub

ErrHandler:
    MsgBox "Erreur d'audit : " & Err.Description, vbCritical, "PlanBA — Audit Métré"
End Sub

Private Function DerniereValeurNumerique(ws As Worksheet, col As Long) As Double
    ' Dernière valeur numérique de la colonne (ligne TOTAL GÉNÉRAL)
    Dim r As Long
    For r = ws.Rows.Count To 1 Step -1
        If IsNumeric(ws.Cells(r, col).Value) And Not IsEmpty(ws.Cells(r, col).Value) Then
            DerniereValeurNumerique = ws.Cells(r, col).Value
            Exit Function
        End If
    Next r
    DerniereValeurNumerique = 0
End Function

Private Function ValeurLigneLibelle(ws As Worksheet, libelle As String, col As Long) As Double
    ' Valeur en colonne col sur la ligne dont la colonne A contient libelle
    Dim trouve As Range
    Set trouve = ws.Columns(1).Find(What:=libelle, LookIn:=xlValues, _
                                    LookAt:=xlPart, MatchCase:=False)
    If trouve Is Nothing Then
        ValeurLigneLibelle = 0
    ElseIf IsNumeric(ws.Cells(trouve.Row, col).Value) Then
        ValeurLigneLibelle = ws.Cells(trouve.Row, col).Value
    Else
        ValeurLigneLibelle = 0
    End If
End Function

Private Function ValeurLignePrix(ws As Worksheet, numPrix As Long, col As Long) As Double
    ' Valeur en colonne col sur la ligne dont la colonne A vaut numPrix
    Dim trouve As Range
    Set trouve = ws.Columns(1).Find(What:=CStr(numPrix), LookIn:=xlValues, _
                                    LookAt:=xlWhole, MatchCase:=False)
    If trouve Is Nothing Then
        ValeurLignePrix = 0
    ElseIf IsNumeric(ws.Cells(trouve.Row, col).Value) Then
        ValeurLignePrix = ws.Cells(trouve.Row, col).Value
    Else
        ValeurLignePrix = 0
    End If
End Function

'------------------------------------------------------------
' 3. RÉINITIALISATION — vide les saisies, conserve formules/mise en page
'------------------------------------------------------------
Public Sub ReinitialiserDonneesTemplate()
    Dim rep As VbMsgBoxResult
    rep = MsgBox("Vider toutes les données de saisie pour un nouveau " & _
                 "chantier ?" & vbCrLf & _
                 "(formules, mise en page et cartouches conservés)", _
                 vbYesNo + vbQuestion, "PlanBA — Réinitialisation")
    If rep <> vbYes Then Exit Sub

    Dim ws1 As Worksheet, ws2 As Worksheet, ws3 As Worksheet, ws4 As Worksheet
    On Error GoTo ErrHandler
    Set ws1 = ThisWorkbook.Worksheets("01_Detail_Quantitatif")
    Set ws2 = ThisWorkbook.Worksheets("02_Armatures")
    Set ws3 = ThisWorkbook.Worksheets("03_Attachement_Ferraillage")
    Set ws4 = ThisWorkbook.Worksheets("04_GO_Attachement")

    Application.ScreenUpdating = False

    ' Feuille 1 : 3 blocs de 8 lignes de saisie (B..I uniquement, J/K = formules)
    ' Bloc 1 : lignes 9-16 | Bloc 2 : lignes 21-28 | Bloc 3 : lignes 33-40
    ws1.Range("B9:I16").ClearContents
    ws1.Range("B21:I28").ClearContents
    ws1.Range("B33:I40").ClearContents

    ' Feuille 2 : données barres (A..I, J..S = formules)
    ws2.Range("A4:I19").ClearContents

    ' Feuille 3 : synthèse (A..F, G..O = formules)
    ws3.Range("A4:F15").ClearContents

    ' Feuille 4 : quantités marché uniquement (E..G = formules liées)
    ws4.Range("D4:D7").ClearContents

    Application.ScreenUpdating = True
    MsgBox "Modèle réinitialisé — prêt pour un nouveau chantier.", _
           vbInformation, "PlanBA — Réinitialisation"
    Exit Sub

ErrHandler:
    Application.ScreenUpdating = True
    MsgBox "Erreur de réinitialisation : " & Err.Description, _
           vbCritical, "PlanBA — Réinitialisation"
End Sub
