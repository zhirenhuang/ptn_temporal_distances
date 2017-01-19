import fnmatch
import pickle
import os

import matplotlib
import numpy
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from scipy.stats import binned_statistic

from util import get_data_or_compute

import settings
from gtfspy.routing.node_profile_analyzer_time_and_veh_legs import NodeProfileAnalyzerTimeAndVehLegs

to_vectors = NodeProfileAnalyzerTimeAndVehLegs.all_measures_and_names_as_lists()
ALL_TO_ALL_STATS_DIR = os.path.join(settings.RESULTS_DIRECTORY, "all_to_all_stats")

from matplotlib import rc

rc('text', usetex=True)

def _get_raw_stats_filenames():
    filenames = [os.path.join(ALL_TO_ALL_STATS_DIR, fname)
                 for fname in os.listdir(ALL_TO_ALL_STATS_DIR)
                 if fnmatch.fnmatch(fname, "*all_to_all_stats_target_*.pkl")]
    filenames = list(sorted(filenames, key=lambda fname: (len(fname), fname)))
    return filenames


def compute_observable_name_matrix(observable_name, limit=None):
    fnames = _get_raw_stats_filenames()
    values = []
    if limit:
        fnames = fnames[:limit]
    for fname in fnames:
        print(fname)
        with open(fname, 'rb') as f:
            data = pickle.load(f)
            values.append(data['stats'][observable_name])
    return numpy.array(values)


def _plot_2d_pdf(xvalues, yvalues, xbins, ybins, aspect='equal', ax=None):
    histogram, xbins, ybins = numpy.histogram2d(xvalues, yvalues, bins=[xbins, ybins], normed=True)

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)
    histogram[histogram == 0] = float('nan')
    cmap = matplotlib.cm.get_cmap("viridis")  # afmhot
    cmap.set_bad("white", 1.)

    extent = [xbins[0], xbins[-1], ybins[0], ybins[-1]]
    im = ax.imshow(histogram.T, interpolation='nearest', origin='low',
                   extent=extent, cmap=cmap, aspect=aspect)

    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.set_label(r"Probability density", size=10)
    cbar.formatter.set_powerlimits((0, 0))
    cbar.ax.yaxis.set_offset_position('left')
    cbar.update_ticks()

    # cbar.ticklabel_format(style='sci', scilimits=(-3,4), axis='y')

    bin_centers, _, _ = binned_statistic(xvalues, xvalues, statistic='mean', bins=xbins)
    bin_averages, _, _ = binned_statistic(xvalues, yvalues, statistic='mean', bins=xbins)
    percentile_5, _, _ = binned_statistic(xvalues, yvalues, statistic=lambda values: numpy.percentile(values, 5),
                                          bins=xbins)
    percentile_95, _, _ = binned_statistic(xvalues, yvalues, statistic=lambda values: numpy.percentile(values, 95),
                                           bins=xbins)
    # bin_medians, _, _ = binned_statistic(xvalues, yvalues, statistic='median', bins=xbins)
    bin_stdevs, _, _ = binned_statistic(xvalues, yvalues, statistic='std', bins=xbins)
    ax.plot(bin_centers, bin_averages, ls="-", lw=3.0, color="red", alpha=0.8, label="mean")
    ax.plot(bin_centers, percentile_5, ls="--", lw=3.0, color="red", alpha=0.8, label="5th and 95th percentile")
    ax.plot(bin_centers, percentile_95, ls="--", lw=3.0, color="red", alpha=0.8)  # , label="95th percentile")
    # ax.plot(bin_centers, bin_medians, ls="--", color="green", label="median")
    ax.set_xlim(0, 180)
    ax.set_ylim(0, 180)
    leg = ax.legend(loc="upper right", fancybox=True, prop={'size': 10})
    leg.get_frame().set_alpha(0.9)
    return ax


def _load_data():
    observables = [
        "min_temporal_distance",
        "mean_temporal_distance",
        "max_temporal_distance",
        "n_pareto_optimal_trips",
        "mean_n_boardings_on_shortest_paths",
        "min_n_boardings",
        "max_n_boardings_on_shortest_paths"
    ]

    observable_to_matrix = {}
    numpy.random.seed(seed=10)
    rands = numpy.unique(numpy.random.randint(1, 5000, size=100))
    for observable in observables:
        matrix = get_data_or_compute(
            os.path.join(ALL_TO_ALL_STATS_DIR, observable + "_matrix.pkl"),
            compute_observable_name_matrix,
            observable,
            recompute=False,
            limit=None
        )
        # print(matrix.shape)
        # print(rands.shape)
        # print("Taking only a small sample for faster plot dev!")
        # matrix = matrix[rands]
        print(matrix.shape)
        observable_to_matrix[observable] = matrix

    print("data loaded")

    mins_flattened = observable_to_matrix["min_temporal_distance"].flatten() / 60.0
    print("mins flattened")

    maxs_flattened = observable_to_matrix["max_temporal_distance"].flatten() / 60.0
    print("maxs flattened")

    means_flattened = observable_to_matrix["mean_temporal_distance"].flatten() / 60.0
    print("means flattened")

    n_trips_flattened = observable_to_matrix["n_pareto_optimal_trips"].flatten()
    print("n_trips flattened")

    mean_n_boardings_flattened = observable_to_matrix["mean_n_boardings_on_shortest_paths"].flatten()
    print("mean_n_boardings flattened")

    min_n_boardings_flattened = observable_to_matrix["min_n_boardings"].flatten()
    max_n_boardings_flattened = observable_to_matrix["max_n_boardings_on_shortest_paths"].flatten()

    time_bins = numpy.linspace(-0.5, 180.5, 182)

    combined_time_valids = numpy.ones(len(mins_flattened), dtype=bool)
    for arr in [mins_flattened, means_flattened, maxs_flattened]:
        time_valids = numpy.ones(len(mins_flattened), dtype=bool)
        time_valids *= (arr >= 0)
        time_valids *= (arr < float('inf'))
        combined_time_valids *= time_valids
        time_invalids = numpy.logical_not(time_valids)
        arr[time_invalids] = 240

    print("Filtered invalid time values")

    # mins_flattened[combined_time_valids] = 240
    # maxs_flattened[combined_time_valids] = 240
    # means_flattened[combined_time_valids] = 240

    mins_flattened_time_valids = mins_flattened[combined_time_valids]
    maxs_flattened_time_valids = maxs_flattened[combined_time_valids]
    means_flattened_time_valids = means_flattened[combined_time_valids]
    mean_n_boardings_flattened_time_valids = mean_n_boardings_flattened[combined_time_valids]
    n_pareto_optimal_trips_flattened_time_valids = n_trips_flattened[combined_time_valids]
    min_n_boardings_flattened_time_valids = min_n_boardings_flattened[combined_time_valids]
    max_n_boardings_flattened_time_valids = max_n_boardings_flattened[combined_time_valids]

    flattened_time_valids = {}
    flattened_time_valids["min_temporal_distance"] = mins_flattened_time_valids
    flattened_time_valids["mean_temporal_distance"] = means_flattened_time_valids
    flattened_time_valids["max_temporal_distance"] = maxs_flattened_time_valids
    flattened_time_valids["mean_n_boardings_on_shortest_paths"] = mean_n_boardings_flattened_time_valids
    flattened_time_valids["n_pareto_optimal_trips"] = n_pareto_optimal_trips_flattened_time_valids
    flattened_time_valids["min_n_boardings"] = min_n_boardings_flattened_time_valids
    flattened_time_valids["max_n_boardings_on_shortest_paths"] = max_n_boardings_flattened_time_valids
    return time_bins, flattened_time_valids


def mean_vs_mean():
    # mean vs. mean
    # this turned to not be really interesting
    # plot symmetricity of observations
    i_to_j = []
    j_to_i = []
    means_mat = observable_to_matrix["mean_temporal_distance"]
    for i in range(len(means_mat)):
        for j in range(i + 1, len(means_mat)):
            ij = means_mat[i, j]
            ji = means_mat[j, i]
            if ij < float('inf') and ji < float('inf') and ij >= 0 and ji >= 0:
                i_to_j.append(means_mat[i, j])
                j_to_i.append(means_mat[j, i])
    fig, ax = _plot_2d_pdf(i_to_j,
                           j_to_i,
                           time_bins,
                           time_bins)
    ax.set_ylabel("mean tdist (i->j)")
    ax.set_xlabel("mean tdist (j->i)")
    leg = ax.legend(loc="best", fancybox=True)
    leg.get_frame().set_alpha(0.8)

    ax.set_xlim([0, 120])
    ax.set_ylim([0, 120])
    ax.yaxis.label.set_size(18)
    ax.xaxis.label.set_size(18)
    fig.savefig(os.path.join(settings.FIGS_DIRECTORY, "all_to_all_mean_vs_mean_symmetricity.pdf"))


def mean_vs_min(xvalues, y_values, x_bins, y_bins):
    fig, ax = _plot_2d_pdf(mins_flattened_time_valids, maxs_flattened_time_valids,
                           time_bins, time_bins)
    ax.set_xlabel("min tdist")
    ax.set_ylabel("maxs tdist")
    ax.plot([0, 180], [0, 180], "--", color="blue", lw=3)
    fig.savefig(os.path.join(settings.FIGS_DIRECTORY, "all_to_all_min_vs_max.pdf"))


def max_vs_min():
    fig, ax = _plot_2d_pdf(mins_flattened_time_valids, means_flattened_time_valids,
                           time_bins, time_bins)
    ax.set_xlabel("mins tdist")
    ax.set_ylabel("means tdist")
    ax.plot([0, 180], [0, 180], "--", color="blue", lw=3)
    fig.savefig(os.path.join(settings.FIGS_DIRECTORY, "all_to_all_min_vs_mean.pdf"))


def mean_vs_max():
    fig, ax = _plot_2d_pdf(means_flattened_time_valids,
                           maxs_flattened_time_valids,
                           time_bins, time_bins)
    ax.set_xlabel("means tdist")
    ax.set_ylabel("maxs tdist")
    ax.plot([0, 180], [0, 180], "--", color="blue", lw=3)
    fig.savefig(os.path.join(settings.FIGS_DIRECTORY, "all_to_all_mean_vs_max.pdf"))


def plot_mean_minus_min_vs_min(ax, mins, means, time_bins):
    _plot_2d_pdf(mins,
                 means - mins,
                 time_bins,
                 time_bins,
                 aspect='auto',
                 ax=ax)
    ax.set_ylabel("$\\tau_\\mathrm{mean} - \\tau_\\mathrm{min}$")
    ax.set_xlabel("$\\tau_\\mathrm{min}$")


def max_minus_min_vs_min():
    fig, ax = _plot_2d_pdf(mins_flattened_time_valids,
                           maxs_flattened_time_valids - mins_flattened_time_valids,
                           time_bins, time_bins)
    ax.set_ylabel("max - min tdist")
    ax.set_xlabel("mins tdist")
    ax.set_xlim([0, 120])
    ax.set_ylim([0, 60])
    fig.savefig(os.path.join(settings.FIGS_DIRECTORY, "all_to_all_max_minus_min_vs_min.pdf"))


def plot_mean_minus_min_per_min_vs_min(ax, mins, means, time_bins):
    valids_zero = mins > 0
    mins_now = mins[valids_zero]
    means_now = means[valids_zero]
    ax = _plot_2d_pdf(mins_now, (means_now - mins_now) / mins_now, time_bins,
                      numpy.linspace(0, 3, 100), aspect='auto', ax=ax)
    ax.set_ylabel("$(\\tau_\\mathrm{mean} - \\tau_\\mathrm{min}) / \\tau_\\mathrm{min}$")
    ax.set_xlabel("$\\tau_\\mathrm{min}$")
    ax.set_xlim([0, 140])
    ax.set_ylim([0, 2])


def plot_min_vs_n_pareto_optimal_journeys(ax, mins, journey_counts, time_bins):
    x_label = "$\\tau_\\mathrm{min}$"
    y_label = "$n_\\mathrm{journeys}$"
    max_n_trips = max(journey_counts)
    n_trip_bins = numpy.linspace(-0.5, max_n_trips + 0.5, max_n_trips + 2)
    ax = _plot_2d_pdf(mins,
                      journey_counts,
                      time_bins,
                      n_trip_bins,
                      aspect='auto',
                      ax=ax)
    ax.set_ylabel(y_label)
    ax.set_xlabel(x_label)
    ax.set_xlim([0, 180])
    ax.set_ylim([0, max_n_trips])


def plot_min_vs_mean_n_boardings(ax, mins, mean_n_boardings, time_bins):
    ax = _plot_2d_pdf(mins,
                      mean_n_boardings,
                      time_bins,
                      numpy.linspace(0, max(mean_n_boardings), 50),
                      aspect='auto',
                      ax=ax)
    ax.set_xlabel("$\\tau_\\mathrm{min}$")
    ax.set_ylabel("$b_\\mathrm{mean\\,f.p.}$")
    ax.set_xlim([0, 180])
    ax.set_ylim([0, max(mean_n_boardings)])


def plot_min_tdist_pdf(ax, min_times, mean_times, max_times, time_bins):
    ax.set_xlabel("Temporal distance $\\tau$ (min)")
    ax.set_ylabel("Probability density $P(\\tau)$")
    ax.set_xlim([0, 180])
    orig_colors = [[237, 248, 177], [127, 205, 187], [44, 127, 184]][::-1]
    alphas = [1.0, 0.8, 0.6] # [1.0, 0.7, 0.4]
    colors = [(r / 256., g / 256., b / 256, alpha) for (r, g, b), alpha in zip(orig_colors, alphas)]
    # colors = ['#edf8b1', '#7fcdbb', '#2c7fb8'][::-1]
    labels = ["$\\tau_\\mathrm{%s}$" % s for s in ["min", "mean", "max"]]
    for values, color, label, lw in zip([min_times, mean_times, max_times], colors, labels, [2, 1.5, 1.]):
        ax.hist(values,
                bins=time_bins,
                facecolor=color,
                edgecolor="k",
                histtype="stepfilled",
                normed=True,
                label=label,
                lw=lw)
    xfmt = ScalarFormatter()
    xfmt.set_powerlimits((-0, 0))
    ax.yaxis.set_major_formatter(xfmt)
    leg = ax.legend(loc="best", fancybox=True)
    leg.get_frame().set_alpha(0.9)


def plot_min_n_boardings_vs_mean_n_boardings(ax, min_nboardings, mean_n_boardings_fp):
    ax = _plot_2d_pdf(min_nboardings,
                      mean_n_boardings_fp - min_nboardings,
                      numpy.linspace(-0.5, 0.5 + numpy.round(max(mean_n_boardings_fp)), numpy.round(max(mean_n_boardings_fp)) + 2),
                      numpy.linspace(0, max(mean_n_boardings_fp), 50),
                      aspect='auto',
                      ax=ax)
    ax.set_xlabel("$b_\\mathrm{min}$")
    ax.set_ylabel("$b_\\mathrm{mean\\,f.p.}$")
    ax.set_xlim([-0.5, max(mean_n_boardings_fp)])
    ax.set_ylim([0, max(mean_n_boardings_fp)])


def plot_boarding_count_distributions(ax, min_nboardings, mean_n_boardings_fp, max_n_boardings_fp):
    ax.set_xlabel("Number of boardings $b$")
    ax.set_ylabel("Probability density $P(b)$")
    orig_colors = [[237, 248, 177], [127, 205, 187], [44, 127, 184]][::-1]
    alphas = [1.0, 0.7, 1.0]
    colors = [(r / 256., g / 256., b / 256, alpha) for (r, g, b), alpha in zip(orig_colors, alphas)]
    # colors = ['#edf8b1', '#7fcdbb', '#2c7fb8'][::-1]
    labels = ["$b_\\mathrm{%s}$" % s for s in ["min", "mean,f.p.", "max,f.p"]]
    max_n = max(max_n_boardings_fp)

    for i, (values, color, label, lw) in enumerate(zip([min_nboardings, mean_n_boardings_fp, max_n_boardings_fp], colors, labels, [2, 1.5, 1.])):
        bin_width = 0.2
        offset = -0.07 * (i - 1)
        bins = numpy.arange(-0.1 + offset, max_n + 0.1 + offset, bin_width)
        if i is 0:
            zorder = -10
        if i is 1:
            zorder = 10
        if i is 2:
            zorder = 0
        ax.hist(values,
                bins=bins,
                facecolor=color,
                edgecolor="k",
                histtype="stepfilled",
                normed=True,
                label=label,
                lw=lw,
                zorder=zorder
                )
    xfmt = ScalarFormatter()
    xfmt.set_powerlimits((-0, 0))
    ax.yaxis.set_major_formatter(xfmt)
    leg = ax.legend(loc="best", fancybox=True)
    leg.get_frame().set_alpha(0.9)
    ax.set_xlim(-0.15, max_n+0.15)




if __name__ == "__main__":
    time_bins, flattened_time_valid_dict = _load_data()
    fig = plt.figure(figsize=(16, 8))

    ax1 = fig.add_subplot(2, 3, 1)
    plot_min_tdist_pdf(ax1,
                       flattened_time_valid_dict["min_temporal_distance"],
                       flattened_time_valid_dict["mean_temporal_distance"],
                       flattened_time_valid_dict["max_temporal_distance"],
                       time_bins[::3])
    print("finished ax1")

    ax2 = fig.add_subplot(2, 3, 2)
    plot_mean_minus_min_vs_min(ax2,
                               flattened_time_valid_dict["min_temporal_distance"],
                               flattened_time_valid_dict["mean_temporal_distance"],
                               time_bins
                               )
    ax2.set_xlim(0, 140)
    ax2.set_ylim(0, 80)
    print("finished ax2")

    ax3 = fig.add_subplot(2, 3, 3)
    plot_mean_minus_min_per_min_vs_min(ax3,
                                       flattened_time_valid_dict["min_temporal_distance"],
                                       flattened_time_valid_dict["mean_temporal_distance"],
                                       time_bins
                                       )
    ax3.set_xlim(0, 140)
    print("finished ax3")

    ax4 = fig.add_subplot(2, 3, 4)
    plot_boarding_count_distributions(ax4,
                                      flattened_time_valid_dict["min_n_boardings"],
                                      flattened_time_valid_dict["mean_n_boardings_on_shortest_paths"],
                                      flattened_time_valid_dict["max_n_boardings_on_shortest_paths"]
                                      )
    print("finished ax4")

    ax5 = fig.add_subplot(2, 3, 5)
    plot_min_vs_mean_n_boardings(ax5,
                                 flattened_time_valid_dict["min_temporal_distance"],
                                 flattened_time_valid_dict["mean_n_boardings_on_shortest_paths"],
                                 time_bins=time_bins)
    ax5.set_xlim(0, 140)
    print("finished ax5")

    ax6 = fig.add_subplot(2, 3, 6)
    plot_min_vs_n_pareto_optimal_journeys(ax6,
                                          flattened_time_valid_dict["min_temporal_distance"],
                                          flattened_time_valid_dict["n_pareto_optimal_trips"],
                                          time_bins=time_bins)
    ax6.set_xlim(0, 140)
    print("finished ax6")

    for ax, letter in zip([ax1, ax2, ax3, ax4, ax5, ax6], "ABCDEF"):
        ax.text(0.04, 0.96, "\\textbf{" + letter + "}",
                horizontalalignment="left",
                verticalalignment="top",
                transform=ax.transAxes,
                fontsize=15,
                color="black",
                backgroundcolor="white")

    fig.tight_layout()
    fig.savefig(settings.FIGS_DIRECTORY + "all_to_all_stats.pdf")
    plt.show()