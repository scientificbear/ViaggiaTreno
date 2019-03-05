library(dplyr)
library(magrittr)
library(lubridate)
library(ggplot2)
library(patchwork)
library(tidyr)
library(tibble)
library(tidygraph)
library(ggraph)
library(extrafont)
library(readr)
library(forcats)

stations <- read_csv("../data/stations.csv") %>%
  rowid_to_column("id_number")

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


# fdate <- "2019-02-22"
# raw_data <- list.files(path="../data/single_train_status", pattern=paste0(fdate,".csv")) %>%
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
geom_histogram(bins = ndays*6)


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
  geom_bar(aes(x=fct_reorder(nomeLungo,count), y=count), stat = "identity") +
  xlab("") +
  ylab("") +
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

raw_data %>%
  filter(!is.na(seg_delay), abs(seg_delay/60)<0.5) %>% 
  ggplot() +
  geom_boxplot(aes(x="", y=seg_delay))

raw_data %>%
  filter(!is.na(seg_delay), abs(seg_delay)<30) %>% 
  ggplot() +
  geom_density(aes(seg_delay), bw=0.3, fill="grey", alpha=.6) +
  geom_vline(xintercept = 0) + 
  theme_minimal()


raw_data %>% filter(!is.na(seg_delay), abs(seg_delay)<60) %>% pull(seg_delay) %>% median()
raw_data %>% filter(!is.na(fin_delay), abs(fin_delay)<120) %>% pull(fin_delay) %>% median()


raw_data %>% 
  filter(!is.na(fin_delay), abs(fin_delay)<120) %>%
  pull(fin_delay) %>% 
  quantile(., seq(0,1,0.001)) %>% 
  plot(seq(0,1,0.001), ., type="l")

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
