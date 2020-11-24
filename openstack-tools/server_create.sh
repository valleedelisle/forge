#source cee-shared-space-openrc.sh
openstack server delete dvalleed-ess-sat --wait;openstack server create --config-drive true --block-device-mapping vdb=94b6de39-6625-4a10-8b4a-4b2744d4a95a --block-device-mapping vdc=30a4aa14-43c9-46ae-9436-f0c0487b2539 --user-data ess-sat-user-data.txt --image RHEL7.8 --flavor quicklab.ocp4.master --nic net-id=External  --security-group open dvalleed-ess-sat --wait
nova get-vnc-console dvalleed-ess-sat novnc
