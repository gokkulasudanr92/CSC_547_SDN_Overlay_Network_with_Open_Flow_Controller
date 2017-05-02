DELIMITER $$

/*
Procedure   : AddVMHost
Parameters  : hostname, private_ip, public_ip, ram_mb, cpu_count, cpu_speed, network_speed, computer_group, vmprofile_name
Description : 
*/

DROP PROCEDURE IF EXISTS AddVMHost$$
CREATE PROCEDURE AddVMHost(
  IN hostname 			varchar(36),
  IN private_ip 		varchar(15),
  IN public_ip			varchar(15),
  IN ram_mb 			mediumint(8),
  IN cpu_count 		tinyint(3),
  IN cpu_speed 		smallint(5),
  IN network_speed 	smallint(3),
  IN computer_group	varchar(50),
  IN vmprofile_name	varchar(56)
)
BEGIN
	SELECT state.id INTO @stateid FROM state WHERE state.name = 'vmhostinuse';
	SELECT user.id INTO @ownerid FROM user, affiliation WHERE user.unityid = 'admin' AND user.affiliationid = affiliation.id AND affiliation.name = 'Local';
	SELECT provisioning.id INTO @provisioningid FROM provisioning WHERE provisioning.name = 'none';
	SELECT resourcetype.id INTO @resourcetypeid FROM resourcetype WHERE resourcetype.name = 'computer';
	SELECT image.id INTO @noimageid FROM image WHERE image.name = 'noimage';
	SELECT imagerevision.id INTO @noimagerevisionid FROM imagerevision WHERE imagerevision.imagename = 'noimage';
	SELECT module.id INTO @predictivemoduleid FROM module WHERE module.name = 'predictive_level_0';
	
	SELECT resourcegroup.id INTO @resourcegroupid FROM resourcegroup WHERE resourcegroup.name = computer_group;
	
	
	SELECT vmprofile.id INTO @vmprofileid FROM vmprofile WHERE vmprofile.profilename = vmprofile_name;
	
	SET @insert_computer = CONCAT(
		'INSERT INTO computer
		(
			hostname,
			privateIPaddress,
			IPaddress,
			RAM,
			procnumber,
			procspeed,
			network,
			stateid,
			ownerid,
			provisioningid,
			currentimageid,
			nextimageid,
			imagerevisionid,
			predictivemoduleid,
			scheduleid
		)
		VALUES
		(',
			QUOTE(hostname)			, ',',
			QUOTE(private_ip)			, ',',
			QUOTE(public_ip)			, ',',
			ram_mb						, ',',
			cpu_count					, ',',
			cpu_speed					, ',',
			network_speed				, ',',
			@stateid						, ',',
			@ownerid						, ',',
			@provisioningid			, ',',
			@noimageid					, ',',
			@noimageid					, ',',
			@noimagerevisionid		, ',',
			@predictivemoduleid		, ',',
			'1'
		')'
	);
	PREPARE insert_computer FROM @insert_computer;
	EXECUTE insert_computer;
	SET @computer_id = LAST_INSERT_ID();
	SELECT CONCAT("inserted into computer table, ID: ", @computer_id) AS '';
	
	SET @insert_resource = CONCAT(
		'INSERT INTO resource
		(
			resourcetypeid,
			subid
		)
		VALUES
		(',
			@resourcetypeid, ',',
			@computer_id,
		')'
	);
	PREPARE insert_resource FROM @insert_resource;
	EXECUTE insert_resource;
	SET @resource_id = LAST_INSERT_ID();
	SELECT CONCAT("inserted into resource table, ID: ", @resource_id) AS '';
	
	SET @insert_resourcegroupmembers = CONCAT(
		'INSERT INTO resourcegroupmembers
		(
			resourceid,
			resourcegroupid
		)
		VALUES
		(',
			@resource_id, ',',
			@resourcegroupid,
		')'
	);
	PREPARE insert_resourcegroupmembers FROM @insert_resourcegroupmembers;
	EXECUTE insert_resourcegroupmembers;
	SET @resourcegroupmembers_id = LAST_INSERT_ID();
	SELECT CONCAT("inserted into resourcegroupmembers table, ID: ", @resourcegroupmembers_id) AS '';
	
	SET @insert_vmhost = CONCAT(
		'INSERT INTO vmhost
		(
			computerid,
			vmlimit,
			vmprofileid
		)
		VALUES
		(',
			@computer_id, ',',
			'99,',
			@vmprofileid,
		')'
	);
	PREPARE insert_vmhost FROM @insert_vmhost;
	EXECUTE insert_vmhost;
	SET @vmhost_id = LAST_INSERT_ID();
	SELECT CONCAT("inserted into vmhost table, ID: ", @vmhost_id) AS '';
	
END$$

--              hostname,  private_ip, public_ip, ram_mb,  cpu_count, cpu_speed, network_speed, computer_group, vmprofile_name
CALL AddVMHost('testhost', '1.1.1.1',  '2.2.2.2', '8192',  4,         2000,      1000,          'allComputers', 'KVM - local storage');
