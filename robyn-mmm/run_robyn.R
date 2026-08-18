#!/usr/bin/env Rscript

# Three-channel Marketing Mix Model using Meta's Robyn package.
#
# Dependent variable: weekly signups
# Paid media exposures: Facebook, PPC, YouTube impressions
# Paid media spend: paired weekly spend for each channel

suppressPackageStartupMessages(library(Robyn))

Sys.setenv(R_FUTURE_FORK_ENABLE = "true")
options(future.fork.enable = TRUE)

project_dir <- normalizePath(
  Sys.getenv("ROBYN_PROJECT_DIR", unset = "."),
  mustWork = TRUE
)

data_path <- file.path(project_dir, "data", "sample_mmm.csv")
output_dir <- file.path(project_dir, "outputs")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

if (!file.exists(data_path)) {
  stop("Input data not found: ", data_path)
}

dt_input <- read.csv(data_path, stringsAsFactors = FALSE)
dt_input$DATE <- as.Date(dt_input$DATE)

required_columns <- c(
  "DATE",
  "signups",
  "facebook_impressions",
  "ppc_impressions",
  "youtube_impressions",
  "facebook_spend",
  "ppc_spend",
  "youtube_spend"
)

missing_columns <- setdiff(required_columns, names(dt_input))
if (length(missing_columns) > 0) {
  stop("Missing required columns: ", paste(missing_columns, collapse = ", "))
}

if (anyNA(dt_input[required_columns])) {
  stop("Input data contains missing values in required columns.")
}

if (any(diff(dt_input$DATE) <= 0)) {
  stop("DATE must be strictly increasing.")
}

if (nrow(dt_input) < 52) {
  warning("Fewer than 52 weekly observations. MMM estimates may be unstable.")
}

media_columns <- c(
  "facebook_impressions",
  "ppc_impressions",
  "youtube_impressions"
)

spend_columns <- c(
  "facebook_spend",
  "ppc_spend",
  "youtube_spend"
)

if (any(dt_input[media_columns] < 0)) {
  stop("Media exposure columns cannot contain negative values.")
}

if (any(dt_input[spend_columns] < 0)) {
  stop("Spend columns cannot contain negative values.")
}

data("dt_prophet_holidays", package = "Robyn")

window_start <- format(min(dt_input$DATE), "%Y-%m-%d")
window_end <- format(max(dt_input$DATE), "%Y-%m-%d")

InputCollect <- robyn_inputs(
  dt_input = dt_input,
  dt_holidays = dt_prophet_holidays,
  date_var = "DATE",
  dep_var = "signups",
  dep_var_type = "conversion",
  prophet_vars = c("trend", "season", "holiday"),
  prophet_country = "US",
  context_vars = NULL,
  paid_media_spends = spend_columns,
  paid_media_vars = media_columns,
  organic_vars = NULL,
  factor_vars = NULL,
  window_start = window_start,
  window_end = window_end,
  adstock = "geometric"
)

# Hyperparameter names must be based on paid_media_vars.
# Digital channels generally receive relatively short geometric carryover ranges.
# YouTube is given a slightly wider starter range to allow longer video carryover.
hyperparameters <- list(
  facebook_impressions_alphas = c(0.5, 3),
  facebook_impressions_gammas = c(0.3, 1),
  facebook_impressions_thetas = c(0, 0.3),

  ppc_impressions_alphas = c(0.5, 3),
  ppc_impressions_gammas = c(0.3, 1),
  ppc_impressions_thetas = c(0, 0.3),

  youtube_impressions_alphas = c(0.5, 3),
  youtube_impressions_gammas = c(0.3, 1),
  youtube_impressions_thetas = c(0, 0.5),

  train_size = c(0.6, 0.8)
)

InputCollect <- robyn_inputs(
  InputCollect = InputCollect,
  hyperparameters = hyperparameters
)

iterations <- as.integer(Sys.getenv("ROBYN_ITERATIONS", unset = "2000"))
trials <- as.integer(Sys.getenv("ROBYN_TRIALS", unset = "5"))
cores_raw <- Sys.getenv("ROBYN_CORES", unset = "")
cores <- if (nzchar(cores_raw)) as.integer(cores_raw) else NULL

if (is.na(iterations) || iterations < 1) {
  stop("ROBYN_ITERATIONS must be a positive integer.")
}
if (is.na(trials) || trials < 1) {
  stop("ROBYN_TRIALS must be a positive integer.")
}
if (!is.null(cores) && (is.na(cores) || cores < 1)) {
  stop("ROBYN_CORES must be a positive integer when supplied.")
}

cat(
  sprintf(
    "Running Robyn with %s rows, %s iterations, and %s trials.\n",
    nrow(dt_input), iterations, trials
  )
)

OutputModels <- robyn_run(
  InputCollect = InputCollect,
  cores = cores,
  iterations = iterations,
  trials = trials,
  ts_validation = TRUE,
  add_penalty_factor = FALSE
)

OutputCollect <- robyn_outputs(
  InputCollect,
  OutputModels,
  pareto_fronts = "auto",
  csv_out = "pareto",
  clusters = TRUE,
  export = TRUE,
  plot_folder = output_dir,
  plot_pareto = TRUE
)

saveRDS(InputCollect, file.path(output_dir, "InputCollect.rds"))
saveRDS(OutputModels, file.path(output_dir, "OutputModels.rds"))
saveRDS(OutputCollect, file.path(output_dir, "OutputCollect.rds"))

cat("\nRobyn run complete.\n")
cat("Review the Pareto model outputs and one-pagers in:\n")
cat(normalizePath(output_dir), "\n")
cat(
  "\nDo not select a model on NRMSE alone. Review decomposition, response curves, ",
  "business plausibility, and calibration evidence where available.\n",
  sep = ""
)
