param(
[string]$svcname
);

#restart-service
#start-service
#stop-service
#add assembly
get-service $svcname | restart-service



