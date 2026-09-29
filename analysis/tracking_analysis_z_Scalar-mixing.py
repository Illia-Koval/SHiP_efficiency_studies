import ROOT
from array import array

events_with_tracks = 0
good_events = 0
reco_events = 0

events_with_n_daughters = [0, 0, 0, 0, 0]

mother_name = "Scalar-mixing"
mode =[ #"mu+mu-"]#, "Pi+Pi-", "e+e-", "K+K-"]#, 
        "2Pi+2Pi-"] #,  will not work
scalar_mass = "0.22"
scalar_mass = "1.8"

treename_signal = "Events" #tree name in the sim file

#filename_signal = "../../EventCalc-SHiP/outputs/Scalar-mixing/eventData/Scalar-mixing_3.000e+00_1.000e+01_data.root" #sim file             add _lots.root for muons
filename_signal = f"../../../EventCalc-SHiP/outputs/{mother_name}/eventData/{mother_name}_{float(scalar_mass):.3e}_1.000e+01_data_{mode[0]}.root" #signal file

#creating dataframe with the tree, useful to loop over entries, making new columns with processed values and stuff
dataframe_signal = ROOT.RDataFrame(treename_signal, filename_signal)
dict_signal = dataframe_signal.AsNumpy(["vtx_x", "vtx_y", "vtx_z", "d_px", "d_py", "d_pz"])

treename_sim = "cbmsim" #tree name in the sim file
filename_sim = f"sim_signal/sim_signal_{mother_name}_" + scalar_mass + f"_GeV_10_m_{mode[0]}.root" #sim file  add _lots.root for muons

#creating dataframe with the tree, useful to loop over entries, making new columns with processed values and stuff
dataframe_sim = ROOT.RDataFrame(treename_sim, filename_sim)
dict_MC = dataframe_sim.AsNumpy(["MCTrack.fTrackID", "MCTrack.fMotherId", "MCTrack.fPdgCode", "strawtubesPoint.fTrackID"])

treename_rec = "ship_reco_sim" #tree name in the reco file                                                                 add _lots_additional_rec.root for muons
filename_rec = f"sim_signal/sim_signal_{mother_name}_" + scalar_mass + f"_GeV_10_m_{mode[0]}_rec.root" #reco file sim_muonback_io.root
dataframe_rec = ROOT.RDataFrame(treename_rec, filename_rec)
dict_rec = dataframe_rec.AsNumpy(["fitTrack2MC"])


#in metres
delta_x_in = 1.
delta_y_in = 2.7
z_min = 33.12 #32.

delta_x_out = 4.
delta_y_out = 6.
z_max = 83.12 #82.

nbins = 10

#!!! must put a constraint on the smaller number of events. Initial for both is 0
total_events = min(int(len(dict_signal["vtx_x"])), int(len(dict_MC["MCTrack.fTrackID"])))
print(total_events)
histogram_total = dataframe_signal.Range(total_events).Histo1D(("vtx_z", "Vertex Z", nbins, z_min, z_max), "vtx_z")


histogram_pass = ROOT.TH1D("vtx_z", "Both mu accepted in geo and MC and reco", nbins, z_min, z_max)
histogram_reconstructible = ROOT.TH1D("vtx_z", "Both mu accepted in geo and MC", nbins, z_min, z_max)

histogram_fail_MC = ROOT.TH1D("vtx_z", "Vertex Z with at least one mu failed", nbins, z_min, z_max)
histogram_fail_reco = ROOT.TH1D("vtx_z", "Vertex Z with at least one mu failed", nbins, z_min, z_max)
histogram_geometrical_acceptance = ROOT.TH1D("vtx_z", "Vertex Z in geometrical acceptance", nbins, z_min, z_max)

hist_stack_fails = ROOT.THStack("hist_stack_fails", "All failed events")

n2 = ROOT.std.vector('int')()
not_enough_daughters = 0

def x_limit(z):
    return (delta_x_in/2 * (z_max - z)/(z_max - z_min) + delta_x_out/2 * (z - z_min)/(z_max - z_min))

def y_limit(z):
    return (delta_y_in/2 * (z_max - z)/(z_max - z_min) + delta_y_out/2 * (z - z_min)/(z_max - z_min))

print("start")

for event in range(total_events):#min(len(dict_signal["vtx_x"]), len(dict_MC["MCTrack.fTrackID"]))):
    ######## geometrical acceptance #########
    
    geometrical_acceptance = False
    #position of the vemin(len(dict_signal["vtx_x"]), len(dict_MC["MCTrack.fTrackID"]))rtex -> initial point for daughters
    x_0 = dict_signal["vtx_x"][event]
    y_0 = dict_signal["vtx_y"][event]
    z_0 = dict_signal["vtx_z"][event]
    if (abs(x_0) > x_limit(z_0) or abs(y_0) > y_limit(z_0) or z_0 < z_min or z_0 > z_max):
        print("vertex out of bounds")
        continue
    nDaughtersGeom = len(dict_signal["d_px"][event])
    daughters_in_acceptance = 0
    #looping over the daughters
    for i in range(nDaughtersGeom):
        #extrapolating the coordinate linearly using the momentum
        scale = (z_max - z_0)/dict_signal["d_pz"][event][i] #(z difference over the momentum)
        x_final = x_0 + scale * dict_signal["d_px"][event][i]
        y_final = y_0 + scale * dict_signal["d_py"][event][i]

        if (abs(x_final) < x_limit(z_max) and abs(y_final) < y_limit(z_max)):
            daughters_in_acceptance += 1
            
    if (daughters_in_acceptance <= nDaughtersGeom):
        events_with_n_daughters[daughters_in_acceptance] += 1
    if nDaughtersGeom != 2: print("weird signal")
    if (daughters_in_acceptance == nDaughtersGeom):
        geometrical_acceptance = True
    

    ######## Both daughter(!) tracks are reconstructible ###########
    
    all_daughters_reconstructible = False
    n2.clear()

    nDaughtersMC = 0
    for track in range(len(dict_MC["MCTrack.fTrackID"][event])): #loops over events(count) and tracks
        if (dict_MC["MCTrack.fMotherId"][event][track] != 0): #avoids looping over tracks that are not from the primary decay
            continue
        nDaughtersMC += 1
        if (abs(dict_MC["MCTrack.fPdgCode"][event][track]) != 13): #debug message just in case, filters muons
            print("issue: daughter not an (anti)muon")
        counter = 0 #number of straw tube hits
        TrackID = dict_MC["MCTrack.fTrackID"][event][track]
        for i in range (len(dict_MC["strawtubesPoint.fTrackID"][event])): #loop over hits for this event
            TubeTrackID = dict_MC["strawtubesPoint.fTrackID"][event][i]
            if (TubeTrackID == TrackID): #this track is in the straw tube
                counter += 1

        if (counter >= 25):
            n2.push_back(int(TrackID))
    
    if(nDaughtersMC != nDaughtersGeom):
        print(f"weird simulation, ID {event}: different daughter number")
        not_enough_daughters += 1
        continue #such event is discarded

    if(len(n2) == nDaughtersMC):
        all_daughters_reconstructible = True
        good_events += 1

    ######## Reconstruction ########
    
    all_daughters_reconstructed = False
      
    
    temp_reco = 0
    for ID in n2:
        for i in range(len(dict_rec["fitTrack2MC"][event])):
            if (dict_rec["fitTrack2MC"][event][i] == ID):
                temp_reco += 1
    if (temp_reco == nDaughtersMC):
        all_daughters_reconstructed = True
        reco_events += 1


    ######## If all three are true, store ########
    if(geometrical_acceptance):
        histogram_geometrical_acceptance.Fill(z_0)
        if (all_daughters_reconstructible):
            histogram_reconstructible.Fill(z_0)
            if (all_daughters_reconstructed):
                histogram_pass.Fill(z_0)
            else: #daughters not reconstructed
                histogram_fail_reco.Fill(z_0)
        else: #not all are reconstructible, but both fly in the frame
            histogram_fail_MC.Fill(z_0)
    else: #not all daughters are in the frame
        not_enough_daughters += 1

print(f"Not enough daughters in frame: {not_enough_daughters}")
print(events_with_n_daughters)

print(histogram_pass.GetBinContent(10), histogram_total.GetBinContent(10), histogram_total.GetEntries())

print(f"events with tracks: {events_with_tracks}")
print(f"good events: {good_events}")
print(f"reco events: {reco_events}")
if (good_events != 0):
    print(f"total efficiency: {reco_events/good_events}")


c = ROOT.TCanvas("c", "c", 900, 700)

#all events at this mass
histogram_total.Draw()
#c.SaveAs("Signal_z.png")

#both daughters in the geometrical acceptance
#histogram_geometrical_acceptance = ROOT.TH1D("vtx_z", "Vertex Z in geometrical acceptance", nbins, z_min, z_max)
#histogram_geometrical_acceptance.Add(histogram_pass, histogram_fails)
histogram_geometrical_acceptance.Draw()
#c.SaveAs("Geometrical_acceptance_z.png")


#efficiency = ROOT.TEfficiency(histogram_reconstructible, histogram_total.GetValue())
#efficiency.SetTitle("Combined efficiency;Vertex Z;Events")
#efficiency.Draw()
#c.SaveAs("Efficiency_z.png")

#both daughters leave reconstructible tracks
histogram_reconstructible.Draw()
#c.SaveAs("Reconstructible_z.png")

#how efficient we get two daughters in MC given we have two daughters in geo
efficiency_geo_to_MC = ROOT.TEfficiency(histogram_reconstructible, histogram_geometrical_acceptance)
efficiency_geo_to_MC.SetTitle("Efficiency (2mu geo acceptance -> 2mu MC reconstructible);Vertex Z;Events")
efficiency_geo_to_MC.Draw()
#c.SaveAs("Efficiency_geo_to_MC_z.png")

#both daughters were reconstructed correctly
histogram_pass.Draw()
#c.SaveAs("Reconstructed_z.png")

#how efficient we get two daughters in reco given we have two daughters in MC
import ROOT

efficiency_MC_to_reco = ROOT.TEfficiency(histogram_pass, histogram_reconstructible)
efficiency_MC_to_reco.SetTitle(";Vertex Z [m];Tracking efficiency")

histogram_background = efficiency_MC_to_reco.GetCopyTotalHisto()

# --- optional: apply the reweighting from part 1 here, before rescaling for display ---
htotal_norm = histogram_total.Clone("htotal_norm")
htotal_norm.Scale(htotal_norm.GetNbinsX() / htotal_norm.Integral())  # mean weight = 1
histogram_background.Divide(htotal_norm)

histogram_background.SetTitle(";Vertex Z [m];Tracking efficiency")
histogram_background.SetStats(False)
histogram_background.SetLineColor(920)
histogram_background.SetFillColor(920)

# remember the true maximum BEFORE rescaling, we need it for the right-hand axis
true_max = histogram_background.GetMaximum()
print(true_max)

histogram_background.Scale(1.0 / true_max)   # now displayed range is 0-1, matching efficiency
histogram_background.GetYaxis().SetRangeUser(0.0, 1.1)
histogram_background.GetXaxis().SetTitleSize(0.07)
histogram_background.GetYaxis().SetTitleSize(0.07)
histogram_background.GetXaxis().SetLabelSize(0.055)
histogram_background.GetYaxis().SetLabelSize(0.055)
histogram_background.GetXaxis().SetTitleOffset(0.95)
histogram_background.GetYaxis().SetTitleOffset(0.8)
histogram_background.GetXaxis().SetTitleFont(42)
histogram_background.GetYaxis().SetTitleFont(42)
histogram_background.GetXaxis().SetLabelFont(42)
histogram_background.GetYaxis().SetLabelFont(42)


c.SetBottomMargin(0.14)
c.SetLeftMargin(0.14)
c.SetTopMargin(0.03)
c.SetRightMargin(0.18)      # widened to fit the new right-hand axis + its title

histogram_background.Draw("HIST")

efficiency_MC_to_reco.SetMarkerStyle(20)
efficiency_MC_to_reco.Draw("SAME")

c.Modified()
c.Update()

# --- right-hand axis: 0 - 1.1 (displayed) maps to 0 - true_max*1.1 (real events) ---
axis_right = ROOT.TGaxis(
    ROOT.gPad.GetUxmax(), 0,
    ROOT.gPad.GetUxmax(), 1.1,
    0, true_max * 1.1,
    510, "+L"
)
axis_right.SetTitle("Reconstructible events")
axis_right.SetTitleFont(42)
axis_right.SetLabelFont(42)
axis_right.SetTitleSize(0.07)
axis_right.SetLabelSize(0.055)
axis_right.SetTitleOffset(1.1)
axis_right.SetLineColor(ROOT.kBlack)
axis_right.SetLabelColor(ROOT.kBlack)
axis_right.SetTitleColor(ROOT.kBlack)
axis_right.Draw()

c.Modified()
c.Update()
c.SaveAs("Efficiency_MC_to_reco_z.png")


#all failed events after geo
legend = ROOT.TLegend(0.45, 0.25)
legend.AddEntry(histogram_fail_MC, "Not all mu reconstructible")
histogram_fail_MC.SetFillColor(46)
hist_stack_fails.Add(histogram_fail_MC)
legend.AddEntry(histogram_fail_reco, "Not all mu reconstructed correctly")
histogram_fail_reco.SetFillColor(30)
hist_stack_fails.Add(histogram_fail_reco)
hist_stack_fails.Draw()
legend.Draw()
#c.SaveAs("Fails_z.png")


#total efficiency
efficiency_total = ROOT.TEfficiency(histogram_reconstructible, histogram_total.GetValue())
efficiency_total.SetTitle("Total efficiency (signal -> reco);Vertex Z;Events")
efficiency_total.Draw()
#c.SaveAs("Efficiency_total_z.png")

histogram_total.Draw()
c.SaveAs("Signal_z.png")

