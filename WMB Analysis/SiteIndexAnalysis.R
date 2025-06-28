library("duckdb")
library("ggplot2")
library("scales")
library("quantreg")
library("svglite")
library("rstatix")
library(dplyr)
library(RColorBrewer)

# connect to database file
drv <- duckdb(dbdir = "vri_analysis.db")
con <- dbConnect(drv)
vri <- dbGetQuery(con, "select SITE_INDEX, POLYGON_AREA, STAND_TYPE_25, SPECIES_CD_1[:2] as LEAD_SPC, DECID_PCT, prod_bin FROM vri WHERE SITE_INDEX IS NOT NULL")
dbDisconnect(con, shutdown=TRUE)

# Group leading species < 1000 total ha
area_sum <- vri %>%
  group_by(LEAD_SPC) %>%
  summarise(total_area = sum(POLYGON_AREA), n=n())
vri <- vri %>%
  left_join(area_sum, by = "LEAD_SPC")
vri <- vri %>%
  mutate(LEAD_SPC_grp = ifelse(total_area < 1500, "Other (P, S, SE, SS, WS)", LEAD_SPC))
vri <- vri %>%
  select(-total_area)

# reorder species for legend
vri$LEAD_SPC_grp <- factor(vri$LEAD_SPC_grp, levels = c("SB","AT","PL","SW","SX","AC","EP","LT","BL","Other (P, S, SE, SS, WS)", NA))

# create subsets for each stand type
conif <- vri[which(vri$STAND_TYPE_25=='Coniferous'), ]
decid <- vri[which(vri$STAND_TYPE_25=='Deciduous'), ]
mixed <- vri[which(vri$STAND_TYPE_25=='Mixed'), ]

# remove polygons with no stand type
vri <- vri[!is.na(vri$STAND_TYPE_25),]

# histogram by stand type
ggplot(vri, aes(x=SITE_INDEX, fill=STAND_TYPE_25))+
  geom_histogram(aes(weight=POLYGON_AREA), color='#22222230', binwidth=1) +
  scale_y_continuous(labels=comma, expand=c(0,0)) +
  scale_x_continuous(expand=c(0,0), breaks = seq(0, 35, by=5)) +
  scale_fill_manual(values = c("#753e91", "#499b46", "#ffff8d")) +
  guides(fill = guide_legend(title="Stand Type (25 - 75% cutoff)")) +
  labs(x="VRI Site Index (m @50bha)", y="Area (ha)") +
  theme_bw() + theme(legend.position=c(0.8, 0.5), panel.border = element_blank(), panel.grid.major = element_blank(), panel.grid.minor = element_blank(), axis.line = element_line(colour = "black"))

# histogram by stand type and leading species
getPalette = colorRampPalette(brewer.pal(8, "Dark2"))
ggplot(vri, aes(x=SITE_INDEX, fill=LEAD_SPC_grp))+
  geom_histogram(aes(weight=POLYGON_AREA), color='#22222230', binwidth=1) +
  scale_y_continuous(labels=comma, expand=c(0,0)) +
  scale_x_continuous(expand=c(0,0)) +
  scale_fill_manual(values= getPalette(10)) +
  guides(fill = guide_legend(title="Leading Species Code")) +
  labs(x="VRI Site Index (m@50bha)", y="Area (ha)") +
  theme_bw() + theme(legend.position="bottom",legend.title = ,panel.border = element_blank(), panel.grid.major = element_blank(), panel.grid.minor = element_blank(), axis.line = element_line(colour = "black"))+
  facet_wrap(vars(STAND_TYPE_25), scales='free')

# same histogram by productivity bin
ggplot(vri, aes(x=SITE_INDEX, fill=prod_bin))+
  geom_histogram(aes(weight=POLYGON_AREA), color='#22222230', binwidth=1) +
  scale_y_continuous(labels=comma, expand=c(0,0)) +
  scale_x_continuous(expand=c(0,0)) +
  scale_fill_manual(values= getPalette(10)) +
  guides(fill = guide_legend(title="Leading Species Code")) +
  labs(x="VRI Site Index (m@50bha)", y="Area (ha)") +
  theme_bw() + theme(legend.position="bottom",legend.title = ,panel.border = element_blank(), panel.grid.major = element_blank(), panel.grid.minor = element_blank(), axis.line = element_line(colour = "black"))+
  facet_wrap(vars(STAND_TYPE_25), scales='free')

# boxplot by stand type - note this is counting number of polygons not area
ggplot(vri,
       aes(
         x=factor(STAND_TYPE_25, levels=c("Coniferous", "Mixed", "Deciduous")),
         y=SITE_INDEX,
         fill=STAND_TYPE_25
         )
       )+
  geom_boxplot(varwidth = TRUE) +
  scale_fill_manual(values = c("#753e91", "#499b46", "#ffff8d"), guide="none") +
  labs(x="Stand Type (25 - 75% cutoff)", y="VRI Site Index (m @50bha)")

# Get outliers from boxplot for each stand composition type
out <- boxplot.stats(conif$SITE_INDEX)$out
out_ind <- which(conif$SITE_INDEX %in% c(out))

# Plot the outliers for each stand type
ggplot(identify_outliers(conif, SITE_INDEX), aes(x=SITE_INDEX, fill=LEAD_SPC))+
  geom_histogram(aes(weight=POLYGON_AREA), color='#22222230', binwidth=1) +
  scale_y_continuous(labels=comma, expand=c(0,0)) +
  scale_x_continuous(expand=c(0,0), breaks = seq(0, 35, by=5)) +  scale_fill_viridis_d() +
  guides(fill = guide_legend(title="Leading Species Code")) +
  labs(x="VRI Site Index (m)", y="Area (ha)", title="Distribution of site index by leading species in outlier coniferous (<25% deciduous) stands")+ 
  theme_bw() + theme(legend.position=c(0.8, 0.5), panel.border = element_blank(), panel.grid.major = element_blank(), panel.grid.minor = element_blank(), axis.line = element_line(colour = "black"))
  
ggplot(identify_outliers(mixed, SITE_INDEX), aes(x=SITE_INDEX, fill=LEAD_SPC))+
  geom_histogram(aes(weight=POLYGON_AREA), color='#22222230', binwidth=1) +
  scale_y_continuous(labels=comma, expand=c(0,0)) +
  scale_x_continuous(expand=c(0,0), breaks = seq(0, 35, by=5)) +  scale_fill_viridis_d() +
  guides(fill = guide_legend(title="Leading Species Code")) +
  labs(x="VRI Site Index (m)", y="Area (ha)", title="Distribution of site index by leading species in outlier mixed (25 - 75% deciduous) stands")+ 
  theme_bw() + theme(legend.position=c(0.5, 0.5), panel.border = element_blank(), panel.grid.major = element_blank(), panel.grid.minor = element_blank(), axis.line = element_line(colour = "black"))

ggplot(identify_outliers(decid, SITE_INDEX), aes(x=SITE_INDEX, fill=LEAD_SPC))+
  geom_histogram(aes(weight=POLYGON_AREA), color='#22222230', binwidth=1) +
  scale_y_continuous(labels=comma, expand=c(0,0)) +
  scale_x_continuous(expand=c(0,0), breaks = seq(0, 35, by=5)) +  scale_fill_viridis_d() +
  guides(fill = guide_legend(title="Leading Species Code")) +
  labs(x="VRI Site Index (m)", y="Area (ha)", title="Distribution of site index by leading species in outlier deciduous (>75% deciduous) stands")+
  theme_bw() + theme(legend.position=c(0.8, 0.8), panel.border = element_blank(), panel.grid.major = element_blank(), panel.grid.minor = element_blank(), axis.line = element_line(colour = "black"))


ggplot(identify_outliers(mixed, SITE_INDEX), aes(x=SITE_INDEX, fill=LEAD_SPC_grp))+
  geom_histogram(aes(weight=POLYGON_AREA), color='#22222230', binwidth=1) +
  scale_y_continuous(labels=comma, expand=c(0,0)) +
  scale_x_continuous(expand=c(0,0), breaks = seq(0, 35, by=5)) +  scale_fill_viridis_d() +
  guides(fill = guide_legend(title="Leading Species Code")) +
  labs(x="VRI Site Index (m)", y="Area (ha)", title="Distribution of site index by leading species in outlier mixed (25 - 75% deciduous) stands") +  
  theme_bw() + theme(legend.position="bottom", panel.border = element_blank(), panel.grid.major = element_blank(), panel.grid.minor = element_blank(), axis.line = element_line(colour = "black"))



# Deciduous percentage distribution by species
ggplot(vri, aes(x=DECID_PCT, fill=LEAD_SPC_grp))+
  geom_histogram(aes(weight=POLYGON_AREA), color='#22222230') +
  scale_y_continuous(labels=comma, expand=c(0,0)) +
  guides(fill = guide_legend(title="Leading Species Code")) +
  labs(x="Deciduous Percent (%)", y="Area (ha)", title="Distribution of Deciduous Percent by leading species in all Mixed stands")

