import ROOT
import numpy as np
from array import array

EventCalc_SHiP_dir = "../../../EventCalc-SHiP"  #relative path to Event Calculator folder
ROOT_files_dir = "sim_signal"                   #relative path to simulation/reco files folder

print_all_histos = False



c = ROOT.TCanvas("c", "c", 900, 700)

#in metres
delta_x_in = 1.
delta_y_in = 2.7
z_min = 33.12 #32.

delta_x_out = 4.
delta_y_out = 6.
z_max = 83.12 #82.

def x_limit(z):
    return (delta_x_in/2 * (z_max - z)/(z_max - z_min) + delta_x_out/2 * (z - z_min)/(z_max - z_min))

def y_limit(z):
    return (delta_y_in/2 * (z_max - z)/(z_max - z_min) + delta_y_out/2 * (z - z_min)/(z_max - z_min))


mother_name = "HNL"
mixing_e = 0.5
mixing_mu = 0.5
mixing_tau = 0
mode = ["Pi+mu-", "Pi-mu+", "K-e+", "K+e-", "Pi+e-", "Pi-e+", "K+mu-", "K-mu+"]
mode_legend_names = ["#pi^{+}#mu^{-}", "#pi^{-}#mu^{+}", "K^{-}e^{+}", "K^{+}e^{-}", "#pi^{+}e^{-}", "#pi^{-}e^{+}", "K^{+}#mu^{-}", "K^{-}#mu^{-}"]


histogram_total = [ROOT.TH1D() for _ in range(len(mode))]

histogram_pass = [ROOT.TH1D() for _ in range(len(mode))]
histogram_reconstructible = [ROOT.TH1D() for _ in range(len(mode))]

histogram_fail_MC = [ROOT.TH1D() for _ in range(len(mode))]
histogram_fail_reco = [ROOT.TH1D() for _ in range(len(mode))]
histogram_geometrical_acceptance = [ROOT.TH1D() for _ in range(len(mode))]

histogram_vertex = [ROOT.TH1D() for _ in range(len(mode))]
efficiency_MC_to_vertex = [ROOT.TH1D() for _ in range(len(mode))]
efficiency_reco_to_vertex = [ROOT.TH1D() for _ in range(len(mode))]

efficiency_geo_to_MC = [ROOT.TEfficiency() for _ in range(len(mode))]
efficiency_MC_to_reco = [ROOT.TEfficiency() for _ in range(len(mode))]
hist_stack_fails = [ROOT.THStack("hist_stack_fails", "All failed events") for _ in range(len(mode))]
efficiency_total = [ROOT.TEfficiency() for _ in range(len(mode))]

for i in range(len(mode)):

    output = open(f"plots/efficiency_mass_scan_{mother_name}_{mode[i]}.txt", "w") #overwrites the content!

    if(mode[i] == "K-e+"):
        masses = ["0.5",  "0.6", "0.7", "0.8", "0.9", "1.0", "1.1", "1.2", "1.3", "1.4"] #+
        nbins = 10
        mass_min = 0.45
        mass_max = 1.45

    if(mode[i] == "K+e-"):
        masses = ["0.5", "0.7", "0.9", "1.1", "1.3"] #+
        nbins = 10
        mass_min = 0.45
        mass_max = 1.45

    if(mode[i] == "K+mu-"):
        masses = ["0.6", "0.7", "0.8", "0.9", "1.0", "1.1", "1.2", "1.3", "1.4"] #+
        nbins = 9
        mass_min = 0.55
        mass_max = 1.45
        
    if(mode[i] == "K-mu+"):
        masses = ["0.6", "0.8", "1.0", "1.2", "1.4"] #+
        nbins = 9
        mass_min = 0.55
        mass_max = 1.45
    
    if(mode[i] == "Pi+e-"):
        masses = ["0.2", "0.35", "0.5",  "0.65", "0.8", "0.95", "1.1", "1.25", "1.4"] #+
        nbins = 9
        mass_min = 0.125
        mass_max = 1.475
        
    if(mode[i] == "Pi-e+"):
        masses = ["0.2", "0.5",  "0.8", "1.1", "1.4"] #+
        nbins = 9
        mass_min = 0.125
        mass_max = 1.475

    if(mode[i] == "Pi+mu-"):
        masses = ["0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0", "1.1", "1.2", "1.3", "1.4"] #+
        nbins = 12
        mass_min = 0.25
        mass_max = 1.45

    if(mode[i] == "Pi-mu+"):
        masses = ["0.3", "0.5",  "0.7", "0.9", "1.1", "1.3"] #+
        nbins = 12
        mass_min = 0.25
        mass_max = 1.45

    histogram_total[i].SetNameTitle("mass", "Signal Events")
    histogram_total[i].SetBins(nbins, mass_min, mass_max)

    histogram_pass[i].SetNameTitle("mass", "Both mu accepted in geo and MC and reco")
    histogram_pass[i].SetBins(nbins, mass_min, mass_max)
    
    histogram_reconstructible[i].SetNameTitle("mass", "Both mu accepted in geo and MC")
    histogram_reconstructible[i].SetBins(nbins, mass_min, mass_max)

    histogram_fail_MC[i].SetNameTitle("mass", "mass with at least one mu failed")
    histogram_fail_MC[i].SetBins(nbins, mass_min, mass_max)
    
    histogram_fail_reco[i].SetNameTitle("mass", "Vertex Z with at least one mu failed")
    histogram_fail_reco[i].SetBins(nbins, mass_min, mass_max)
    
    histogram_geometrical_acceptance[i].SetNameTitle("vtx_z", "Vertex Z in geometrical acceptance")
    histogram_geometrical_acceptance[i].SetBins(nbins, mass_min, mass_max)

    histogram_vertex[i].SetNameTitle("vtx_z", "Reconstructed vertex;Mass [GeV];")
    histogram_vertex[i].SetBins(nbins, mass_min, mass_max)

    n2 = ROOT.std.vector('int')()
    reco_fit_order = ROOT.std.vector('int')()

    print(f"start mode {mode[i]}")

    for scalar_mass in masses:
    
        events_with_tracks = 0
        good_events = 0
        reco_events = 0
        reco_vertices = 0
        events_with_n_daughters = [0, 0, 0]
        not_enough_daughters = 0

        treename_signal = "Events" #tree name in the sim file
        filename_signal = (f"{EventCalc_SHiP_dir}/outputs/{mother_name}/eventData/{mother_name}_{float(scalar_mass):.3e}_1.000e+01_{mixing_e:.3e}_{mixing_mu:.3e}_{mixing_tau:.3e}_data_{mode[i]}.root") #signal file

        #creating dataframe with the tree, useful to loop over entries, making new columns with processed values and stuff
        dataframe_signal = ROOT.RDataFrame(treename_signal, filename_signal)
        dict_signal = dataframe_signal.AsNumpy(["vtx_x", "vtx_y", "vtx_z", "d_px", "d_py", "d_pz", "LLP_m"])

    
        #edit path here
        treename_sim = "cbmsim" #tree name in the sim file
        filename_sim = f"{ROOT_files_dir}/sim_signal_{mother_name}_" + str(mixing_e) + "_"+ str(mixing_mu) + "_" + str(mixing_tau) + "_" + scalar_mass + f"_GeV_10_m_{mode[i]}.root" #sim file
        dataframe_sim = ROOT.RDataFrame(treename_sim, filename_sim)
        dict_MC = dataframe_sim.AsNumpy(["MCTrack.fTrackID", "MCTrack.fMotherId", "MCTrack.fPdgCode", "strawtubesPoint.fTrackID"])
    
        #edit path here
        treename_rec = "ship_reco_sim" #tree name in the reco file
        filename_rec = f"{ROOT_files_dir}/sim_signal_{mother_name}_" + str(mixing_e) + "_"+ str(mixing_mu) + "_" + str(mixing_tau) + "_" + scalar_mass + f"_GeV_10_m_{mode[i]}_rec.root" #reco file sim_muonback_io.root
        dataframe_rec = ROOT.RDataFrame(treename_rec, filename_rec)
        dict_rec = dataframe_rec.AsNumpy(["fitTrack2MC", "Particles.fVz"])

        #Claude-written reading the problematic branch with daughters forming tracks
        f = ROOT.TFile.Open(filename_rec)
        tree = f.Get(treename_rec)

        daughter_pairs = []
        for entry in tree:
            pairs = [(p.GetDaughter(0), p.GetDaughter(1)) for p in entry.Particles]
            daughter_pairs.append(pairs)

        dict_rec["daughterPairs"] = np.array(daughter_pairs, dtype=object)
        f.Close()

        #signal is overgenerated typically by a factor of 2; must put a constraint on the smaller number of events. Initial for both is 0
        total_events = min(int(len(dict_signal["vtx_x"])), int(len(dict_MC["MCTrack.fTrackID"])))

        for event in range(total_events):
            m = dict_signal["LLP_m"][event]
            histogram_total[i].Fill(m)

            ######## geometrical acceptance #########
    
            geometrical_acceptance = False
            #vertex coordinate
            x_0 = dict_signal["vtx_x"][event]
            y_0 = dict_signal["vtx_y"][event]
            z_0 = dict_signal["vtx_z"][event]
            if (abs(x_0) > x_limit(z_0) or abs(y_0) > y_limit(z_0) or z_0 < z_min or z_0 > z_max):
                print("vertex out of bounds")
                continue
            nDaughtersGeom = len(dict_signal["d_px"][event])
            daughters_in_acceptance = 0
            #looping over the daughters
            for idx in range(nDaughtersGeom):
                #extrapolating the coordinate linearly using the momentum
                scale = (z_max - z_0)/dict_signal["d_pz"][event][idx] #(z difference over the momentum)
                x_final = x_0 + scale * dict_signal["d_px"][event][idx]
                y_final = y_0 + scale * dict_signal["d_py"][event][idx]

                if (abs(x_final) < x_limit(z_max) and abs(y_final) < y_limit(z_max)):
                    daughters_in_acceptance += 1
            
            #write down how many daughters are in the frame
            if (daughters_in_acceptance <= nDaughtersGeom):
                events_with_n_daughters[daughters_in_acceptance] += 1
            #all daughters are in geometrical acceptance
            if (daughters_in_acceptance == nDaughtersGeom):
                geometrical_acceptance = True
    

            ######## Both daughter(!) tracks are reconstructible ###########
    
            all_daughters_reconstructible = False
            n2.clear()

            nDaughtersMC = 0
            #loop over tracks in the event
            for track in range(len(dict_MC["MCTrack.fTrackID"][event])): #loops over events(count) and tracks
                if (dict_MC["MCTrack.fMotherId"][event][track] != 0): #avoids looping over tracks that are not from the primary decay
                    continue
                nDaughtersMC += 1
                counter = 0 #number of straw tube hits for this track
                TrackID = dict_MC["MCTrack.fTrackID"][event][track]
                for i_hit in range (len(dict_MC["strawtubesPoint.fTrackID"][event])): #loop over hits for this event
                    TubeTrackID = dict_MC["strawtubesPoint.fTrackID"][event][i_hit]
                    if (TubeTrackID == TrackID): #this track is in the straw tube
                        counter += 1

                #reconstructible track criterion
                if (counter >= 25): #reconstructible track criterion
                    n2.push_back(int(TrackID))

            #for some reason, in the event not all daughter particles were tracked
            if(nDaughtersMC != nDaughtersGeom):
                not_enough_daughters += 1
                continue #such event is discarded

            if(len(n2) == nDaughtersMC):
                all_daughters_reconstructible = True
                good_events += 1

            ######## Reconstruction ########
        
            all_daughters_reconstructed = False
            vertex_reconstructed = False
            reco_fit_order.clear()

            for ID in n2:
                for i_track in range(len(dict_rec["fitTrack2MC"][event])):
                    if (dict_rec["fitTrack2MC"][event][i_track] == ID):
                        reco_fit_order.push_back(i_track) #record the analog of goodTracks in the reco file, but only the daughters here, 0 1 or 1 0 for two-body
                        break

            if (len(reco_fit_order) == nDaughtersMC):
                all_daughters_reconstructed = True
                reco_events += 1

            match = True
            for k in range(len(dict_rec["daughterPairs"][event])): #loop over the pairs of daughters forming vertices
                #try this vertex - check if both daughters form it
                for reco_ID in reco_fit_order:
                    if (reco_ID == dict_rec["daughterPairs"][event][k][0] or reco_ID == dict_rec["daughterPairs"][event][k][1]): #one of the particles in the pair is correct
                        match = match and True #if one of them was False, the other won't change it to true
                    else: #one of the daughters is missing from the pair -> this vertex cannot be true
                        match = False
                        
                if (match == True): #the vertex formed by daughter particles was found
                    if (len(dict_rec["Particles.fVz"][event]) > 1):
                        pass
                        #print(f"event {event} in mode {mode[i]} has additional vertices")
                    vertex_reconstructed = True
                    reco_vertices += 1
                    break


            ######## If all three are true, store ########
            if(geometrical_acceptance):
                histogram_geometrical_acceptance[i].Fill(m)
                if (all_daughters_reconstructible):
                    histogram_reconstructible[i].Fill(m)
                    if (all_daughters_reconstructed):
                        histogram_pass[i].Fill(m)
                        if (vertex_reconstructed):
                            histogram_vertex[i].Fill(m)
                    else: #daughters not reconstructed
                        histogram_fail_reco[i].Fill(m)
                else: #not all are reconstructible, but both fly in the frame
                    histogram_fail_MC[i].Fill(m)
            else: #not all daughters are in the frame
                not_enough_daughters += 1

        print(f"Not enough daughters in frame for mass {scalar_mass} GeV: {not_enough_daughters}")
        print(events_with_n_daughters)
        print(f"events with tracks: {events_with_tracks}")
        print(f"good events: {good_events}")
        print(f"reco events: {reco_events}")
        print(f"reco vertices: {reco_vertices}")
        if (good_events != 0):
            print(f"reco efficiency: {reco_events/good_events}")
            print(f"total vertexing efficiency: {reco_vertices/good_events}")

        output.write(f"Mass: {scalar_mass} GeV: {not_enough_daughters}")
        output.write(f"[0, 1, 2] daughters in acceptance: {events_with_n_daughters}")    
        output.write(f"events with tracks: {events_with_tracks}")
        output.write(f"good events: {good_events}")
        output.write(f"reco events: {reco_events}")
        output.write(f"reco vertices: {reco_vertices}")
        if (good_events != 0):
            output.write(f"reco efficiency: {reco_events/good_events}")
            output.write(f"total vertexing efficiency: {reco_vertices/good_events}")
        output.write("-"*30)
        output.write("\n")

    output.close()

    #all events at this mass
    histogram_total[i].Draw()
    if (print_all_histos):
        c.SaveAs(f"plots/{mother_name}_Signal_{mode[i]}_M.png")

    #all daughters in the geometrical acceptance
    histogram_geometrical_acceptance[i].Draw()
    if (print_all_histos):
        c.SaveAs(f"plots/{mother_name}_Geometrical_acceptance_{mode[i]}_M.png")

    #all daughters leave reconstructible tracks
    histogram_reconstructible[i].Draw()
    if (print_all_histos):
        c.SaveAs(f"plots/{mother_name}_Reconstructible_{mode[i]}_M.png")

    #how efficient we get all daughters in MC given we have all daughters in geo
    efficiency_geo_to_MC[i] = ROOT.TEfficiency(histogram_reconstructible[i], histogram_geometrical_acceptance[i])
    efficiency_geo_to_MC[i].SetTitle("Efficiency (all geo acceptance -> all MC reconstructible);Mass [GeV];Efficiency")
    efficiency_geo_to_MC[i].Draw()
    if (print_all_histos):
        c.SaveAs(f"plots/{mother_name}_Efficiency_geo_to_MC_{mode[i]}_M.png")

    #all daughters were reconstructed correctly
    histogram_pass[i].Draw()
    if (print_all_histos):
        c.SaveAs(f"plots/{mother_name}_Reconstructed_{mode[i]}_M.png")

    #how efficient we get two daughters in reco given we have two daughters in MC
    efficiency_MC_to_reco[i] = ROOT.TEfficiency(histogram_pass[i], histogram_reconstructible[i])
    efficiency_MC_to_reco[i].SetTitle(";HNL mass [GeV];Efficiency")
    efficiency_MC_to_reco[i].Draw()
    if (print_all_histos):
        c.SaveAs(f"plots/{mother_name}_Efficiency_MC_to_reco_{mode[i]}_M.png")


    #all failed events after geo
    legend = ROOT.TLegend(0.55, 0.75, 0.95, 0.95)
    legend.AddEntry(histogram_fail_MC[i], "Not all reconstructible")
    histogram_fail_MC[i].SetFillColor(46)
    hist_stack_fails[i].Add(histogram_fail_MC[i])
    legend.AddEntry(histogram_fail_reco[i], "Not all reconstructed correctly")
    histogram_fail_reco[i].SetFillColor(30)
    hist_stack_fails[i].Add(histogram_fail_reco[i])
    hist_stack_fails[i].Draw()
    legend.Draw()
    if (print_all_histos):
        c.SaveAs(f"plots/{mother_name}_Fails_{mode[i]}_M.png")


    #total efficiency
    efficiency_total[i] = ROOT.TEfficiency(histogram_reconstructible[i], histogram_total[i])
    efficiency_total[i].SetTitle("Total efficiency (signal -> reco);Mass [GeV];Efficiency")
    efficiency_total[i].Draw()
    if (print_all_histos):
        c.SaveAs(f"plots/{mother_name}_Efficiency_total_{mode[i]}_M.png")

    #all events with the reconstructed vertex with two daughters
    histogram_vertex[i].Draw()
    if (print_all_histos):
        c.SaveAs(f"plots/{mother_name}_Vertex_{mode[i]}_M.png")

    #vertexing efficiency
    efficiency_MC_to_vertex[i] = ROOT.TEfficiency(histogram_vertex[i], histogram_reconstructible[i])
    efficiency_MC_to_vertex[i].SetTitle(";HNL mass [GeV];Vertexing efficiency")
    efficiency_MC_to_vertex[i].Draw()
    if (print_all_histos):
        c.SaveAs(f"plots/{mother_name}_Efficiency_MC_to_vertex_{mode[i]}_M.png")

    efficiency_reco_to_vertex[i] = ROOT.TEfficiency(histogram_vertex[i], histogram_pass[i])
    efficiency_reco_to_vertex[i].SetTitle(";HNL mass [GeV];Vertexing efficiency")
    efficiency_reco_to_vertex[i].Draw()
    if (print_all_histos):
        c.SaveAs(f"plots/{mother_name}_Efficiency_reco_to_vertex_{mode[i]}_M.png")


#combined efficiencies of the modes

colours = [ROOT.kBlue+1, ROOT.kRed+1, ROOT.kGreen+2, ROOT.kOrange+7, ROOT.kMagenta+2]
line_styles = [1, 2]

########   combined tracking efficiency   ########
legend = ROOT.TLegend(0.6, 0.25, 0.95, 0.55)
legend.SetTextFont(12)
legend.SetTextSize(0.05)
legend.SetNColumns(2)    

for i, eff in enumerate(efficiency_MC_to_reco):
    mode_idx = i // 2       # 0,0,1,1,2,2,3,3 -> which of the 4 modes
    charge_idx = i % 2      # 0,1,0,1,...     -> charge conjugation
    eff.SetLineColor(colours[mode_idx])
    eff.SetLineStyle(line_styles[charge_idx])
    eff.SetLineWidth(2)
    legend.AddEntry(eff, mode_legend_names[i])
    eff.Draw("A" if i == 0 else "SAME")

c.Update()  # forces ROOT to paint the TEfficiency and create the underlying TGraphAsymmErrors


graph = efficiency_MC_to_reco[0].GetPaintedGraph()
if graph:
    graph.SetMinimum(0.58)   # adjust as needed, e.g. slightly below your lowest curve
    graph.SetMaximum(1.005)  # efficiencies are ~[0,1], add a little headroom
    graph.GetXaxis().SetTitleSize(0.07)
    graph.GetYaxis().SetTitleSize(0.07)
    graph.GetXaxis().SetLabelSize(0.055)
    graph.GetYaxis().SetLabelSize(0.055)
    graph.GetYaxis().SetTitleOffset(0.95)
    graph.GetXaxis().SetTitleOffset(0.95)
    c.Update()

legend.Draw()
c.SetBottomMargin(0.14)
c.SetLeftMargin(0.14)
c.SetTopMargin(0.03)
c.SetRightMargin(0.03)
c.Modified()
c.Update()
c.SaveAs(f"plots/{mother_name}_Efficiency_combined.png")


########   combined vertexing efficiency   ########
#legend = ROOT.TLegend(0.6, 0.25, 0.95, 0.55)
#legend.SetTextFont(12)
#legend.SetTextSize(0.05)
#legend.SetNColumns(2)    
legend.Clear()

for i, eff in enumerate(efficiency_MC_to_vertex):
    mode_idx = i // 2       # 0,0,1,1,2,2,3,3 -> which of the 4 modes
    charge_idx = i % 2      # 0,1,0,1,...     -> charge conjugation
    eff.SetLineColor(colours[mode_idx])
    eff.SetLineStyle(line_styles[charge_idx])
    eff.SetLineWidth(2)
    legend.AddEntry(eff, mode_legend_names[i])
    eff.Draw("A" if i == 0 else "SAME")

c.Update()  # forces ROOT to paint the TEfficiency and create the underlying TGraphAsymmErrors


graph = efficiency_MC_to_vertex[0].GetPaintedGraph()
if graph:
    graph.SetMinimum(0.58)   # adjust as needed, e.g. slightly below your lowest curve
    graph.SetMaximum(1.005)  # efficiencies are ~[0,1], add a little headroom
    graph.GetXaxis().SetTitleSize(0.07)
    graph.GetYaxis().SetTitleSize(0.07)
    graph.GetXaxis().SetLabelSize(0.055)
    graph.GetYaxis().SetLabelSize(0.055)
    graph.GetYaxis().SetTitleOffset(0.95)
    graph.GetXaxis().SetTitleOffset(0.95)
    c.Update()

legend.Draw()
c.SetBottomMargin(0.14)
c.SetLeftMargin(0.14)
c.SetTopMargin(0.03)
c.SetRightMargin(0.03)
c.Modified()
c.Update()
c.SaveAs(f"plots/{mother_name}_Efficiency_combined_vertex.png")
