library(data.table)
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
stations <- read_csv("data/stations.csv") %>%
  rowid_to_column("id_number")


raw_data <- list.files(path="data/single_train_status", pattern="*.csv") %>% 
  paste0("data/single_train_status/", .) %>% 
  lapply(., fread) %>% 
  do.call(rbind, .) %>% 
  mutate(incoming_delay = as.numeric(incoming_delay),
         segment_delay = as.numeric(segment_delay),
         final_delay = as.numeric(final_delay))
head(raw_data)

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
