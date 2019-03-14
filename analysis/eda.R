library(dplyr)
library(magrittr)
library(lubridate)
library(ggplot2)
library(patchwork)
library(tidyr)
library(tibble)
library(tidygraph)
library(ggraph)
# library(extrafont)
library(readr)
library(forcats)
library(stringr)
library(leaflet)


stations <- read_csv("../data/stations.csv") %>%
  rowid_to_column("id_number")

stations %>% 
  ggplot(aes(lon,lat)) +
  geom_point(size=.3) + 
  coord_fixed() + 
  theme_minimal()

df <- list.files(path="../data/train_status", pattern="*.csv") %>% 
  paste0("../data/train_status/", .) %>% 
  lapply(., function(x) read.csv(x, stringsAsFactors = FALSE)) %>% 
  do.call(rbind, .) %>% 
  mutate(trip_date = as.Date(trip_date))

df %>% head()

df %>% 
  ggplot() +
  geom_bar(aes(trip_date)) +
  xlab("date") + 
  ylab(("number of trains")) +
  theme_minimal()

df %>% 
  group_by(category) %>% 
  summarise(count = n()) %>% 
  mutate(count = count/sum(count)) %>% 
  ggplot(aes(x=fct_reorder(category, count), y=count)) +
  geom_col() +
  geom_text(aes(y = count + 0.02, label = paste0(round(100*count), "%"))) +
  xlab("") + 
  ylab(("")) +
  ggtitle("% of trains by class type") +
  scale_y_continuous(labels = scales::percent_format(accuracy = 1)) +
  coord_flip() +
  theme_minimal() +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
        axis.title.x=element_blank(), axis.text.x=element_blank(), axis.ticks.x=element_blank())

ndays <- df %>% pull(trip_date) %>% n_distinct()
df %>% 
  group_by(num_stops) %>% 
  summarise(count = n()/ndays) %>% 
  ggplot(aes(x=num_stops, y=count)) +
  geom_col() + 
  xlab("number of stops") + 
  ylab(("(avg) number of trains per day")) +
  theme_minimal() +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank())

df %>% 
  group_by(origin) %>% 
  summarise(count = n()/ndays) %>% 
  arrange(desc(count)) %>% 
  head(20) %>% 
  ggplot() +
  geom_bar(aes(x=fct_reorder(origin,count), y=count), stat = "identity") +
  ylab("(avg) number of trains") +
  xlab("Starting station") +
  ggtitle("Number of trains by starting station (top 20)") +
  coord_flip() +
  theme_minimal() +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank())





setwd("~/Documents/repos/ViaggiaTreno/analysis")


# fdate <- "2019-02-24"
# raw_data <- list.files(path="../data/single_train_status", pattern=paste0(fdate,".csv")) %>%
#   paste0("../data/single_train_status/", .) %>%
#   lapply(., function(x) read.csv(x, stringsAsFactors = FALSE)) %>%
#   do.call(rbind, .) %>%
#   mutate(trip_date = as.Date(trip_date),
#          from_planned_ts = as_datetime(from_planned-60*60*24*7*2, tz="Europe/Rome"),
#          from_real_ts = as_datetime(from_real-60*60*24*7*2, tz="Europe/Rome"),
#          to_planned_ts = as_datetime(to_planned-60*60*24*7*2, tz="Europe/Rome"),
#          to_real_ts = as_datetime(to_real-60*60*24*7*2, tz="Europe/Rome"),
#          inc_delay = as.numeric(inc_delay),
#          seg_delay = as.numeric(seg_delay),
#          fin_delay = as.numeric(fin_delay))
# 
# 
# raw_data %>% head()
# 
# raw_data[date(raw_data$from_planned_ts)!=as.Date(fdate) & !is.na(raw_data$from_planned_ts), c("inc_delay", "seg_delay", "from_planned")] <- NA
# raw_data[date(raw_data$from_real_ts)!=as.Date(fdate)  & !is.na(raw_data$from_real_ts), c("inc_delay", "seg_delay", "from_real")] <- NA
# raw_data[date(raw_data$to_real_ts)!=as.Date(fdate) & !is.na(raw_data$to_real_ts), c("fin_delay", "seg_delay", "to_real")] <- NA
# raw_data[date(raw_data$to_planned_ts)!=as.Date(fdate) & !is.na(raw_data$to_planned_ts), c("fin_delay", "seg_delay", "to_planned")] <- NA
# 
# raw_data %>% select(-from_planned_ts, -from_real_ts, -to_planned_ts, -to_real_ts) %>% write.csv(paste0('../data/single_train_status/', fdate,'.csv'), row.names = F, quote = FALSE)

# list.files(path="../data/single_train_status", pattern=paste0(fdate,".csv")) %>%
#   paste0("../data/single_train_status/", .) %>%
#   lapply(., function(x) read.csv(x, stringsAsFactors = FALSE)) %>%
#   do.call(rbind, .) %>%
#   mutate(trip_date = as.Date(trip_date),
#          from_planned_ts = as_datetime(from_planned, tz="Europe/Rome"),
#          from_real_ts = as_datetime(from_real, tz="Europe/Rome"),
#          to_planned_ts = as_datetime(to_planned, tz="Europe/Rome"),
#          to_real_ts = as_datetime(to_real, tz="Europe/Rome"),
#          inc_delay = as.numeric(inc_delay),
#          seg_delay = as.numeric(seg_delay),
#          fin_delay = as.numeric(fin_delay)) %>%
#   summary()
# 






raw_data <- list.files(path="../data/single_train_status", pattern="*.csv") %>% 
  paste0("../data/single_train_status/", .) %>% 
  lapply(., function(x) read.csv(x, stringsAsFactors = FALSE)) %>% 
  do.call(rbind, .) %>% 
  mutate(trip_date = as.Date(trip_date),
         from_planned = as_datetime(from_planned, tz="Europe/Rome"),
         from_real = as_datetime(from_real, tz="Europe/Rome"),
         to_planned = as_datetime(to_planned, tz="Europe/Rome"),
         to_real = as_datetime(to_real, tz="Europe/Rome"),
         inc_delay = as.numeric(inc_delay)/60,
         seg_delay = as.numeric(seg_delay)/60,
         fin_delay = as.numeric(fin_delay)/60)

raw_data %>% summary()

raw_data %>% 
  ggplot(aes(x=from_planned)) +
  geom_histogram(bins = ndays*6) +
  theme_minimal() + 
  ggtitle("Number of observations by time")


raw_data %>% 
  filter(step %% 2 != 0) %>% 
  group_by(from_id) %>% 
  summarise(count = n()) %>% 
  arrange(desc(count)) %>% 
  head(20) %>% 
  left_join(stations, by=c("from_id"="id")) %>% 
  mutate(nomeLungo = ifelse(is.na(nomeLungo),from_id,nomeLungo)) %>% 
  select(nomeLungo, count) %>% 
  ggplot() +
  geom_bar(aes(x=fct_reorder(nomeLungo,count), y=count/ndays), stat = "identity") +
  xlab("") +
  ylab("Number of trains (daily)") +
  ggtitle("Number of trains by station (top 20)") +
  coord_flip() +
  theme_minimal() +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank())

raw_data %>% 
  filter(step %% 2 != 0) %>% 
  mutate(from_planned = as.factor(hour(from_planned))) %>% 
  group_by(from_planned) %>% 
  summarise(unique_trains = n_distinct(train_number)) %>% 
  filter(!is.na(from_planned)) %>% 
  ggplot() +
  geom_bar(aes(x=from_planned, y=unique_trains), stat = "identity") +
  xlab("") +
  ylab("") +
  ggtitle("Number of trains by hour of the day") +
  theme_minimal() +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank())

raw_data %<>% 
  filter(!is.na(seg_delay), abs(seg_delay)<100, abs(fin_delay)<180)

temp <- raw_data %>%
  filter(!is.na(seg_delay), abs(seg_delay)<100, abs(fin_delay)<180) %>% 
  mutate(perc_inc_delay = percent_rank(inc_delay),
         perc_seg_delay = percent_rank(seg_delay),
         perc_fin_delay = percent_rank(fin_delay)) %>% 
  select(inc_delay, perc_inc_delay, seg_delay, perc_seg_delay, fin_delay, perc_fin_delay) %>% 
  gather("key_perc", "value_perc", -c("inc_delay", "seg_delay", "fin_delay")) %>% 
  gather("key", "value", -c("key_perc", "value_perc")) %>% 
  mutate(key_perc = str_replace_all(key_perc, "^perc_", "")) %>% 
  filter(key_perc == key) %>% 
  mutate(key = fct_relevel(key, "inc_delay", "seg_delay", "fin_delay")) %>% 
  mutate(a = row_number()) %>% filter(a %% 100 == 0)

max_min <- 60
min_min <- -30

(
  temp %>% 
    ggplot() +
    geom_density(aes(value, fill=key, color=key), alpha=.4) +
    geom_vline(xintercept = 0) + 
    scale_color_brewer(palette="Set2") +
    scale_fill_brewer(palette="Set2") +
    ggtitle("Overall train punctuality") +
    xlab("minutes") +
    scale_x_continuous(limits = c(min_min, max_min)) +
    theme_minimal() +
    theme(legend.position = "none")
) + (
  temp %>% 
    ggplot() +
    geom_boxplot(aes(y=value, x=key, color=key)) +
    geom_hline(yintercept = 0) +
    scale_color_brewer(palette="Set2") +
    scale_fill_brewer(palette="Set2") +
    ylab("minutes") +
    xlab("") +
    scale_y_continuous(limits = c(min_min, max_min)) +
    coord_flip() +
    theme_minimal() +
    theme(legend.position = "none")
) + (
  temp %>% 
    ggplot() +
    geom_line(aes(value, value_perc, color=key), size=1) +
    geom_vline(xintercept = 0) + 
    scale_color_brewer(palette="Set2") +
    xlab("minutes") +
    ylab("cumulative") + 
    scale_x_continuous(limits = c(min_min, max_min)) +
    theme_minimal() +
    theme(legend.position = "bottom")
) + plot_layout(ncol = 1, heights = c(1, 1))

temp <- raw_data %>%
  filter(train_number==9747) %>%
  filter(!is.na(seg_delay), abs(seg_delay)<100, abs(fin_delay)<180) %>% 
  mutate(perc_inc_delay = percent_rank(inc_delay),
         perc_seg_delay = percent_rank(seg_delay),
         perc_fin_delay = percent_rank(fin_delay)) %>% 
  select(inc_delay, perc_inc_delay, seg_delay, perc_seg_delay, fin_delay, perc_fin_delay) %>% 
  gather("key_perc", "value_perc", -c("inc_delay", "seg_delay", "fin_delay")) %>% 
  gather("key", "value", -c("key_perc", "value_perc")) %>% 
  mutate(key_perc = str_replace_all(key_perc, "^perc_", "")) %>% 
  filter(key_perc == key) %>% 
  mutate(key = fct_relevel(key, "inc_delay", "seg_delay", "fin_delay")) 

max_min <- 60
min_min <- -10

(
  temp %>% 
    ggplot() +
    geom_density(aes(value, fill=key, color=key), alpha=.4) +
    geom_vline(xintercept = 0) + 
    scale_color_brewer(palette="Set2") +
    scale_fill_brewer(palette="Set2") +
    ggtitle("Train 9747 (TO > VE, late afternoon) punctuality") +
    xlab("minutes") +
    scale_x_continuous(limits = c(min_min, max_min)) +
    theme_minimal() +
    theme(legend.position = "none")
) + (
  temp %>% 
    ggplot() +
    geom_boxplot(aes(y=value, x=key, color=key)) +
    geom_hline(yintercept = 0) +
    scale_color_brewer(palette="Set2") +
    scale_fill_brewer(palette="Set2") +
    ylab("minutes") +
    xlab("") +
    scale_y_continuous(limits = c(min_min, max_min)) +
    coord_flip() +
    theme_minimal() +
    theme(legend.position = "none")
) + (
  temp %>% 
    ggplot() +
    geom_line(aes(value, value_perc, color=key), size=1) +
    geom_vline(xintercept = 0) + 
    scale_color_brewer(palette="Set2") +
    xlab("minutes") +
    ylab("cumulative") + 
    scale_x_continuous(limits = c(min_min, max_min)) +
    theme_minimal() +
    theme(legend.position = "bottom")
) + plot_layout(ncol = 1, heights = c(1, 1))


temp <- raw_data %>%
  filter(train_number==9747) %>%
  filter(!is.na(seg_delay), abs(seg_delay)<100, abs(fin_delay)<180) %>% 
  left_join(., stations %>% select(id, nomeBreve), by=c("from_id"="id")) %>% 
  rename("from"="nomeBreve") %>% 
  left_join(., stations %>% select(id, nomeBreve), by=c("to_id"="id")) %>% 
  rename("to"="nomeBreve") %>% 
  mutate(segment = ifelse(from==to, from, paste0(from, " > ", to)),
         segment = fct_reorder(segment, -step)) %>% 
  select(trip_date, step, segment, fin_delay)

temp %>% 
  ggplot(aes(x=segment, y=fin_delay, group=trip_date)) +
  geom_hline(yintercept = 0, col="red") +
  geom_line(alpha=.4) +
  stat_summary(aes(x=segment, y=fin_delay, group=segment), fun.y = "median", colour = "red", geom = "point") +
  ylab("delay") + 
  ggtitle("Train 9747 (To > Ve)") +
  coord_flip() +
  theme_minimal()

library(purrr)
p <- c(0.025, 0.05, 0.25, 0.50, 0.75, 0.95, 0.975)
p_names <- map_chr(p, ~paste0("perc_", .x*1000))
p_funs <- map(p, ~partial(quantile, probs = .x, na.rm = TRUE)) %>% 
  set_names(nm = p_names)

(
  raw_data %>%
    filter(train_number==9747) %>%
    filter(!is.na(seg_delay), abs(seg_delay)<100, abs(fin_delay)<180) %>% 
    left_join(., stations %>% select(id, nomeBreve), by=c("from_id"="id")) %>% 
    rename("from"="nomeBreve") %>% 
    left_join(., stations %>% select(id, nomeBreve), by=c("to_id"="id")) %>% 
    rename("to"="nomeBreve") %>% 
    mutate(segment = ifelse(from==to, from, paste0(from, " > ", to)),
           segment = strtrim(segment, 30),
           segment = fct_reorder(segment, -step)) %>% 
    select(trip_date, step, segment, fin_delay) %>% 
    group_by(segment) %>% 
    summarize_at(vars(fin_delay), funs(!!!p_funs)) %>%
    ggplot(aes(x=segment, group=1)) +
    # geom_line(data = temp, aes(x=segment, y=fin_delay, group=trip_date), alpha=.2) +
    geom_ribbon(aes(ymin=`perc_25`, ymax=`perc_975`), alpha=.15) + 
    geom_ribbon(aes(ymin=`perc_50`, ymax=`perc_950`), alpha=.15) +
    geom_ribbon(aes(ymin=`perc_250`, ymax=`perc_750`), alpha=.15) +
    geom_line(aes(y=perc_500)) +
    ylab("delay (min)") +
    scale_y_continuous(limits = c(-10, 60)) +
    coord_flip() +
    theme_minimal()
) + (
  raw_data %>%
    filter(train_number==10918) %>%
    filter(!is.na(seg_delay), abs(seg_delay)<100, abs(fin_delay)<180) %>% 
    left_join(., stations %>% select(id, nomeBreve), by=c("from_id"="id")) %>% 
    rename("from"="nomeBreve") %>% 
    left_join(., stations %>% select(id, nomeBreve), by=c("to_id"="id")) %>% 
    rename("to"="nomeBreve") %>% 
    mutate(segment = ifelse(from==to, from, paste0(from, " > ", to)),
           segment = strtrim(segment, 30),
           segment = fct_reorder(segment, -step)) %>% 
    select(trip_date, step, segment, fin_delay) %>% 
    group_by(segment) %>% 
    summarize_at(vars(fin_delay), funs(!!!p_funs)) %>%
    ggplot(aes(x=segment, group=1)) +
    # geom_line(data = temp, aes(x=segment, y=fin_delay, group=trip_date), alpha=.2) +
    geom_ribbon(aes(ymin=`perc_25`, ymax=`perc_975`), alpha=.15) + 
    geom_ribbon(aes(ymin=`perc_50`, ymax=`perc_950`), alpha=.15) +
    geom_ribbon(aes(ymin=`perc_250`, ymax=`perc_750`), alpha=.15) +
    geom_line(aes(y=perc_500)) +
    ylab("delay (min)") +
    scale_y_continuous(limits = c(-10, 60)) +
    coord_flip() +
    theme_minimal()
)



#














raw_data %<>% 
  mutate(trip_date = ymd(trip_date),
         from_planned_ts = as_datetime(from_planned_ts),
         from_real_ts = as_datetime(from_real_ts),
         to_planned_ts = as_datetime(to_planned_ts),
         to_real_ts = as_datetime(to_real_ts))
raw_data %>% head() %>% View()

section_data <- raw_data %>% 
  group_by(from_id, to_id) %>% 
  summarise(avg_incoming_delay = median(incoming_delay, na.rm = T),
            sd_incoming_delay = sd(incoming_delay, na.rm = T),
            avg_segment_delay = median(segment_delay, na.rm = T),
            sd_segment_delay = sd(segment_delay, na.rm = T),
            avg_final_delay = median(final_delay, na.rm = T),
            sd_final_delay = sd(final_delay, na.rm = T),
            n_rows = n()) %>% 
  ungroup()

section_data %<>%
  inner_join(., stations %>% select(id, id_number), by=c("from_id"="id")) %>% 
  rename(from=id_number) %>% 
  inner_join(., stations %>% select(id, id_number), by=c("to_id"="id")) %>% 
  rename(to=id_number)


p1 <- ggplot(section_data, aes(n_rows)) + geom_density(fill="black") + theme_minimal()
p2 <- ggplot(section_data, aes(y=n_rows, group=1)) + geom_boxplot() + theme_minimal()
p1+p2

avg_delay <- section_data %>% 
  select(-contains("sd_"), -n_rows, -from, -to) %>% 
  gather(key = "measure", value="value", -from_id, -to_id) %>% 
  na.omit() %>% 
  as.data.frame()

p1 <- ggplot(avg_delay, aes(value, fill=measure)) + 
  geom_density(alpha=.5) + 
  theme_minimal() + 
  theme(legend.position = "none")
p2 <- ggplot(avg_delay, aes(y=value, group=measure, fill=measure)) + 
  geom_boxplot(alpha=.5) + 
  coord_flip() + 
  theme_minimal() + 
  theme(legend.position = "bottom")
p1 + p2 + plot_layout(ncol = 1)

edges <- section_data %>% 
  select(from, to, avg_final_delay, sd_final_delay, n_rows)

routes_tidy <- tbl_graph(nodes = stations, edges = edges, directed = FALSE)


selected_regions <- c('Veneto')

routes_tidy %>% 
  activate(nodes) %>% 
  mutate(centrality = centrality_authority()) %>% 
  filter(region %in% selected_regions) %>% 
  ggraph(layout = "manual",
         node.positions = stations %>%
           filter(region %in% selected_regions) %>%
           select(lon, lat) %>% 
           rename(x=lon, y=lat)) + 
  geom_edge_link() + 
  geom_node_text(aes(label=name, size = centrality, colour = centrality)) +
  scale_color_continuous(guide = 'legend') + 
  theme_graph()
