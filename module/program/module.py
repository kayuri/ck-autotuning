#
# Collective Knowledge (program)
#
# See CK LICENSE.txt for licensing details
# See CK COPYRIGHT.txt for copyright details
#
# Developer: Grigori Fursin, Grigori.Fursin@cTuning.org, http://fursin.net
#

cfg={}  # Will be updated by CK (meta description of this module)
work={} # Will be updated by CK (temporal data)
ck=None # Will be updated by CK (initialized CK kernel) 

# Local settings
sep='***************************************************************************************'

##############################################################################
# Initialize module

def init(i):
    """

    Input:  {}

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """
    return {'return':0}

##############################################################################
# compile program

def process(i):
    """
    Input:  {
              sub_action   - clean, compile, run

              (repo_uoa)   - program repo UOA
              (module_uoa) - program module UOA
              data_uoa     - program data UOA

              (host_os)        - host OS (detect, if omitted)
              (target_os)      - OS module to check (if omitted, analyze host)
              (device_id)      - device id if remote (such as adb)

              (process_in_tmp)       - (default 'yes') - if 'yes', clean, compile and run in the tmp directory 
              (tmp_dir)              - (default 'tmp') - if !='', use this tmp directory to clean, compile and run
              (generate_rnd_tmp_dir) - if 'yes', generate random tmp directory

            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              Output of the last compile from function 'process_in_dir'

              tmp_dir      - directory where clean, compile, run
            }

    """

    import os
    import copy

    ic=copy.deepcopy(i)

    # Check if global writing is allowed
    r=ck.check_writing({})
    if r['return']>0: return r

    o=i.get('out','')

    a=i.get('repo_uoa','')
    m=i.get('module_uoa','')
    duoa=i.get('data_uoa','')

    lst=[]

    if duoa=='':
       # First, try to detect CID in current directory
       r=ck.cid({})
       if r['return']==0:
          xruoa=r.get('repo_uoa','')
          xmuoa=r.get('module_uoa','')
          xduoa=r.get('data_uoa','')

          rx=ck.access({'action':'load',
                        'module_uoa':xmuoa,
                        'data_uoa':xduoa,
                        'repo_uoa':xruoa})
          if rx['return']==0 and rx['dict'].get('program','')=='yes':
             duoa=xduoa
             m=xmuoa
             a=xruoa

       if duoa=='':
          # Attempt to load configuration from the current directory
          p=os.getcwd()

          pc=os.path.join(p, ck.cfg['subdir_ck_ext'], ck.cfg['file_meta'])
          if os.path.isfile(pc):
             r=ck.load_json_file({'json_file':pc})
             if r['return']==0 and r['dict'].get('program','')=='yes':
                d=r['dict']

                ii=copy.deepcopy(ic)
                ii['path']=p
                ii['meta']=d
                return process_in_dir(ii)

          return {'return':1, 'error':'data UOA is not defined'}

    # Check wildcards
    r=ck.list_data({'repo_uoa':a, 'module_uoa':m, 'data_uoa':duoa})
    if r['return']>0: return r

    lst=r['lst']
    if len(lst)==0:
       return {'return':1, 'error':'no program(s) found'}

    r={'return':0}
    for ll in lst:
        p=ll['path']

        ruid=ll['repo_uid']
        muid=ll['module_uid']
        duid=ll['data_uid']

        r=ck.access({'action':'load',
                     'repo_uoa':ruid,
                     'module_uoa':muid,
                     'data_uoa':duid})
        if r['return']>0: return r

        d=r['dict']

        if o=='con':
           ck.out('')

        ii=copy.deepcopy(ic)
        ii['meta']=d

        # Check if base_uoa suggests to use another program path
        buoa=d.get('base_uoa','')
        if buoa!='':
           rx=ck.access({'action':'find',
                         'module_uoa':muid,
                         'data_uoa':buoa})
           if rx['return']>0:
              return {'return':1, 'error':'problem finding base entry '+buoa+' ('+rx['error']+')'}

           p=rx['path']

        ii['path']=p
        ii['repo_uoa']=ruid
        ii['module_uoa']=muid
        ii['data_uoa']=duid
        r=process_in_dir(ii)
        if r['return']>0: return r

    return r      

##############################################################################
# compile program  (called from universal function here)

def process_in_dir(i):
    """
    Input:  {
              Comes from 'compile', 'run' and 'clean' functions

              sub_action             - clean, compile, run

              (host_os)              - host OS (detect, if omitted)
              (target_os)            - OS module to check (if omitted, analyze host)
              (device_id)            - device id if remote (such as adb)

              path                   - path
              meta                   - program description

              (generate_rnd_tmp_dir) - if 'yes', generate random tmp directory to compile and run program
                                       (useful during crowd-tuning)

              (compiler_vars)        - dict with set up compiler flags (-D var)
                                       they will update the ones defined as default in program description ...

              (remove_compiler_vars) - list of compiler vars to remove

              (extra_env_for_compilation) - set environment variables before compiling program

              (flags)                - compile flags
              (lflags)               - link flags

              (speed)                - if 'yes', compile for speed (use env CK_OPT_SPEED from compiler)
              (size)                 - if 'yes', compile for size (use env CK_OPT_SIZE from compiler)

              (compile_type)         - static or dynamic (dynamic by default;
                                         however takes compiler default_compile_type into account)
                  or
              (static or dynamic)

              (repeat)               - repeat kernel via environment CT_REPEAT_MAIN if supported

              (sudo)                 - if 'yes', force using sudo 
                                       (if not set up in OS, use ${CK_SUDO_INIT}, ${CK_SUDO_PRE}, ${CK_SUDO_POST})

              (affinity)             - set processor affinity for tihs program run (if supported by OS - see "affinity" in OS)
                                       examples: 0 ; 0,1 ; 0-3 ; 4-7  (the last two can be useful for ARM big.LITTLE arhictecture

              (clean)                - if 'yes', clean tmp directory before using
              (skip_clean_after)     - if 'yes', do not remove run batch

              (repo_uoa)             - program repo UOA
              (module_uoa)           - program module UOA
              (data_uoa)             - program data UOA

              (misc)                 - misc  dict
              (characteristics)      - characteristics/features/properties
              (env)                  - preset environment

              (post_process_script_uoa) - run script from this UOA
              (post_process_subscript)  - subscript name
              (post_process_params)     - (string) add params to CMD

              (deps)                 - already resolved deps (useful for auto-tuning)

              (extra_env)            - extra environment before running code as string
              (pre_run_cmd)          - pre CMD for binary
              (extra_run_cmd)        - extra CMD (can use $#key#$ for autotuning)
              (run_cmd_substitutes)  - dict with substs ($#key#$=value) in run CMD (useful for CMD autotuning)

              (console)              - if 'yes', output to console

              (skip_device_init)     - if 'yes', do not initialize device

              (skip_calibration)     - if 'yes', skip execution time calibration (make it around 4.0 sec)
              (calibration_time)     - calibration time in string, 4.0 sec. by default
              (calibration_max)      - max number of iterations for calibration, 10 by default

              (pull_only_timer_files) - if 'yes', pull only timer files, but not output files 
                                        (useful for remove devices during statistical repetition)

              (energy)                - if 'yes', start energy monitoring (if supported) using script ck-set-power-sensors
                                       Also, set compiler var CK_MONITOR_ENERGY=1 and run-time var CK_MONITOR_ENERGY=1

                                       Note: files, monitored for energy, are defined in system environment.
                                             For example, odroid .profile as:
                                               export CK_ENERGY_FILES="/sys/bus/i2c/drivers/INA231/3-0040/sensor_W;/sys/bus/i2c/drivers/INA231/3-0041/sensor_W;/sys/bus/i2c/drivers/INA231/3-0044/sensor_W;/sys/bus/i2c/drivers/INA231/3-0045/sensor_W;"

              (run_output_files)              - extra list of output files (useful to add in pipeline to collect profiling from Android mobile, for example)

              (extra_post_process_cmd)        - append at the end of execution bat (for example, to call gprof ...)

              (statistical_repetition_number) - int number of current (outside) statistical repetition
                                                to avoid pushing data to remote device if !=0 ...
              (autotuning_iteration)          - int number of current autotuning iteration
                                                to avoid pushing some data to remote device if !=0 ...
              (skip_dataset_copy)             - if 'yes', dataset stays the same across iterations of pipeline, so do not copy to remote again

              (unparsed)                      - if executing ck run program ... -- (unparsed params), add them to compile or run ...

              (compile_timeout)               - (sec.) - kill compile job if too long
              (run_timeout)                   - (sec.) - kill run job if too long
            }

    Output: {
              return          - return code =  0, if successful
                                            >  0, if error
              (error)         - error text if return > 0

              misc            - updated misc dict
              characteristics - updated characteristics
              env             - updated environment
              deps            - resolved deps, if any
            }

    """
    import os
    import time
    import sys
    import shutil
    import time

    start_time=time.time()

    sys.stdout.flush()

    o=i.get('out','')

    sa=i['sub_action']

    sdi=i.get('skip_device_init','')

    sca=i.get('skip_clean_after','')

    grtd=i.get('generate_rnd_tmp_dir','')

    misc=i.get('misc',{})
    ccc=i.get('characteristics',{})
    env=i.get('env',{})
    deps=i.get('deps',{})

    rof=i.get('run_output_files',[])
    eppc=i.get('extra_post_process_cmd','')

    unparsed=i.get('unparsed', [])
    sunparsed=''
    for q in unparsed:
        if sunparsed!='': sunparsed+=' '
        sunparsed+=q

    ee=i.get('extra_env','')
    ercmd=i.get('extra_run_cmd','')
    prcmd=i.get('pre_run_cmd','')
    rcsub=i.get('run_cmd_substitutes','')

    cons=i.get('console','')

    flags=i.get('flags','')
    lflags=i.get('lflags','')
    cv=i.get('compiler_vars',{})
    rcv=i.get('remove_compiler_vars',[])
    eefc=i.get('extra_env_for_compilation',{})

    fspeed=i.get('speed','')
    fsize=i.get('size','')

    xrepeat=i.get('repeat','')
    if xrepeat=='': xrepeat='-1'
    repeat=int(xrepeat)

    me=i.get('energy','')

    xcto=i.get('compile_timeout','')
    xrto=i.get('run_timeout','')

    pp_uoa=i.get('post_process_script_uoa','')
    pp_name=i.get('post_process_subscript','')
    pp_params=i.get('post_process_params','')

    # Check host/target OS/CPU
    hos=i.get('host_os','')
    tos=i.get('target_os','')
    tdid=i.get('device_id','')

    # Get some info about platforms
    ii={'action':'detect',
        'module_uoa':cfg['module_deps']['platform.os'],
        'host_os':hos,
        'target_os':tos,
        'device_id':tdid,
        'skip_device_init':sdi}

    if sa=='run': 
       x='no'
       if i.get('skip_info_collection','')!='': x=i['skip_info_collection']
       ii['skip_info_collection']=x
       ii['out']=o
    else:
       ii['skip_info_collection']='yes'

    r=ck.access(ii)
    if r['return']>0: return r

    hos=r['host_os_uid']
    hosx=r['host_os_uoa']
    hosd=r['host_os_dict']

    tos=r['os_uid']
    tosx=r['os_uoa']
    tosd=r['os_dict']

    bhos=hosd.get('base_uid','')
    if bhos=='': bhos=hos
    bhosx=hosd.get('base_uoa','')
    if bhosx=='': bhosx=hosx
    btos=tosd.get('base_uid','')
    if btos=='': btos=tos
    btosx=tosd.get('base_uoa','')
    if btosx=='': btosx=tosx

    if r['device_id']!='': tdid=r['device_id']
    xtdid=''
    if tdid!='': xtdid=' -s '+tdid

    remote=tosd.get('remote','')

    tbits=tosd.get('bits','')

    # update misc
    misc['host_os_uoa']=hosx
    misc['target_os_uoa']=tosx
    misc['target_os_bits']=tbits
    misc['device_id']=tdid

    # Check compile type
    ctype=i.get('compile_type','')
    if i.get('static','')=='yes': ctype='static'
    if i.get('dynamic','')=='yes': ctype='dynamic'
    # On default Android-32, use static by default 
    # (old platforms has problems with dynamic)
    if ctype=='':
       if tosd.get('default_compile_type','')!='':
          ctype=tosd['default_compile_type']
       else:
          ctype='dynamic'

    # Get host platform type (linux or win)
    rx=ck.get_os_ck({})
    if rx['return']>0: return rx
    hplat=rx['platform']

    bbp=hosd.get('batch_bash_prefix','')
    rem=hosd.get('rem','')
    eset=hosd.get('env_set','')
    etset=tosd.get('env_set','')
    svarb=hosd.get('env_var_start','')
    svarb1=hosd.get('env_var_extra1','')
    svare=hosd.get('env_var_stop','')
    svare1=hosd.get('env_var_extra2','')
    scall=hosd.get('env_call','')
    sdirs=hosd.get('dir_sep','')
    sdirsx=tosd.get('remote_dir_sep','')
    if sdirsx=='': sdirsx=sdirs
    stdirs=tosd.get('dir_sep','')
    sext=hosd.get('script_ext','')
    sexe=hosd.get('set_executable','')
    se=tosd.get('file_extensions',{}).get('exe','')
    sbp=hosd.get('bin_prefix','')
    stbp=tosd.get('bin_prefix','')
    sqie=hosd.get('quit_if_error','')
    evs=hosd.get('env_var_separator','')
    envsep=hosd.get('env_separator','')
    envtsep=tosd.get('env_separator','')
    eifs=hosd.get('env_quotes_if_space','')
    eifsc=hosd.get('env_quotes_if_space_in_call','')
    eifsx=tosd.get('remote_env_quotes_if_space','')
    if eifsx=='': eifsx=eifsc
    wb=tosd.get('windows_base','')
    stro=tosd.get('redirect_stdout','')
    stre=tosd.get('redirect_stderr','')
    ubtr=hosd.get('use_bash_to_run','')
    no=tosd.get('no_output','')
    bex=hosd.get('batch_exit','')

    md5sum=hosd.get('md5sum','')

    ########################################################################
    p=i['path']
    meta=i['meta']

    ruoa=i.get('repo_uoa', '')
    muoa=i.get('module_uoa', '')
    duoa=i.get('data_uoa', '')

    target_exe=meta.get('target_file','')
    if target_exe=='':
       target_exe=cfg.get('target_file','')
    if meta.get('skip_bin_ext','')!='yes':
       target_exe+=se

    # If muoa=='' assume program
    if muoa=='':
       muoa=work['self_module_uid']

    if duoa=='':
       x=meta.get('backup_data_uid','')
       if x!='':
          duoa=meta['backup_data_uid']

    # Reuse compile deps in run (useful for large benchmarks such as SPEC where compile and run is merged)
    rcd=meta.get('reuse_compile_deps_in_run','')

    # Check if compile in tmp dir
    cdir=p
    os.chdir(cdir)

    ########################################################################
    # Check affinity
    aff=i.get('affinity','')
    if aff!='':
       aff=tosd.get('set_affinity','').replace('$#ck_affinity#$',aff)

    ########################################################################
    # Check sudo

    sudo_init=tosd.get('sudo_init','')
    if sudo_init=='': sudo_init=svarb+svarb1+'CK_SUDO_INIT'+svare1+svare
    sudo_pre=tosd.get('sudo_pre','')
    if sudo_pre=='': sudo_pre=svarb+svarb1+'CK_SUDO_PRE'+svare1+svare
#    sudo_post=tosd.get('sudo_post','')
#    if sudo_post=='': 
    sudo_post=svarb+svarb1+'CK_SUDO_POST'+svare1+svare

    isd=i.get('sudo','')
    if isd=='': isd=tosd.get('force_sudo','')

    srn=ck.get_from_dicts(i, 'statistical_repetition_number', '', None)
    if srn=='': srn=0
    else: srn=int(srn)

    ati=ck.get_from_dicts(i, 'autotuning_iteration', '', None)
    if ati=='': ati=0
    else: ati=int(ati)

    sdc=ck.get_from_dicts(i, 'skip_dataset_copy', '', None)

    ##################################################################################################################
    ################################### Clean ######################################
    if sa=='clean':
       # Get host platform type (linux or win)
       cmd=cfg.get('clean_cmds',{}).get(hplat)

       if o=='con':
          ck.out(cmd)
          ck.out('')

       if ubtr!='': cmd=ubtr.replace('$#cmd#$',cmd)
       rx=os.system(cmd)

       # Removing tmp directories
       curdir=os.getcwd()
       for q in os.listdir(curdir):
           if not os.path.isfile(q) and q.startswith('tmp'):
              shutil.rmtree(q, ignore_errors=True)

       return {'return':0}

    # Check tmp dir ...
    x=i.get('process_in_tmp','').lower()
    if x=='': x='yes'

    if x!='yes':
       x=meta.get('process_in_tmp','').lower()

    td=''
    if x=='yes':
       tdx=i.get('tmp_dir','')
       td=tdx
       if td=='': td='tmp'

       if i.get('clean','')=='yes':
          if td!='' and os.path.isdir(td):
             shutil.rmtree(td, ignore_errors=True)

       if tdx=='' and grtd=='yes':
          # Generate tmp dir
          import tempfile
          fd, fn=tempfile.mkstemp(suffix='', prefix='tmp-ck-')
          os.close(fd)
          os.remove(fn)
          td=os.path.basename(fn)

       cdir=os.path.join(p, td)

    misc['tmp_dir']=td
    misc['path']=p

    if cdir!='' and not os.path.isdir(cdir):
       time.sleep(1)
       try:
          os.makedirs(cdir)
       except Exception as e:
          pass
       if not os.path.isdir(cdir):
          return {'return':1, 'error':'can\'t create tmp directory ('+cdir+')'}

    sb='' # Batch

    if o=='con':
       ck.out(sep)
       ck.out('Current directory: '+cdir)
       ck.out('')

    odir=os.getcwd()

    os.chdir(cdir)
    rcdir=os.getcwd()

    # If run and dynamic or reuse compile deps, check deps prepared by compiler
    fdeps=cfg.get('deps_file','')
    if len(deps)==0 and sa=='run' and (rcd=='yes' or ctype=='dynamic'):
       if os.path.isfile(fdeps):
          if o=='con':
             ck.out('')
             ck.out('Reloading depedencies from compilation '+fdeps+' ...')

          rx=ck.load_json_file({'json_file':fdeps})
          if rx['return']>0: return rx
          deps=rx['dict']

    # If compile type is dynamic, reuse deps even for run (to find specific DLLs) 
    # (REMOTE PLATFORMS ARE NOT SUPPORTED AT THE MOMENT, USE STATIC COMPILATION)
#    if (ctype=='dynamic' or sa=='compile' or rcd=='yes'):
       # Resolve deps (unless should be explicitly ignored, such as when installing local version with all dependencies set)

    if len(deps)==0: 
       deps=meta.get('compile_deps',{})

    if len(deps)>0:
       if o=='con':
          ck.out(sep)

       ii={'action':'resolve',
           'module_uoa':cfg['module_deps']['env'],
           'host_os':hos,
           'target_os':tos,
           'device_id':tdid,
           'deps':deps,
           'add_customize':'yes'}
       if o=='con': ii['out']='con'

       rx=ck.access(ii)
       if rx['return']>0: return rx

       if sa=='compile' or remote!='yes':
          sb+=no+rx['bat']

       deps=rx['deps'] # Update deps (add UOA)

    if sa=='compile':
       rx=ck.save_json_to_file({'json_file':fdeps, 'dict':deps})
       if rx['return']>0: return rx

    # If compiler, load env
    comp=deps.get('compiler',{})
    comp_uoa=comp.get('uoa','')
    dcomp={}

    if comp_uoa!='':
       rx=ck.access({'action':'load',
                     'module_uoa':cfg['module_deps']['env'],
                     'data_uoa':comp_uoa})
       if rx['return']>0: return rx
       dcomp=rx['dict']

    # Add energy monitor, if needed and if supported
    sspm1=tosd.get('script_start_power_monitor','')
    sspm2=tosd.get('script_stop_power_monitor','')

    if me=='yes' and sspm1!='':
       if o=='con':
          ck.out('')
          ck.out('Adding energy monitor')
          ck.out('')

       sb+='\n'
       sb+=scall+' '+sspm1+'\n'
       sb+='\n'

    ##################################################################################################################
    ################################### Compile ######################################
    if sa=='compile':
       # Clean target file
       if target_exe!='' and os.path.isfile(target_exe):
          os.remove(target_exe)

    if sa=='compile' or sa=='get_compiler_version':
       # Add compiler dep again, if there
       cb=deps.get('compiler',{}).get('bat','')
       if cb!='' and not sb.endswith(cb):
          sb+='\n'+no+cb.strip()+' 1\n' # We set 1 to tell environment that it should set again even if it was set before

       # Add env
       for k in sorted(env):
           v=env[k]

           if eifs!='' and wb!='yes':
              if v.find(' ')>=0 and not v.startswith(eifs):
                 v=eifs+v+eifs

           sb+=no+eset+' '+k+'='+str(v)+'\n'
       sb+='\n'

       # Try to detect version
       csd=deps.get('compiler',{}).get('dict',{})
       csuoa=csd.get('soft_uoa','')
       if csuoa!='':
          r=ck.access({'action':'detect',
                       'module_uoa':cfg['module_deps']['soft'],
                       'uoa':csuoa,
                       'env':cb,
                       'con':o})
          if r['return']==0:
             cver=r['version_str']
             misc['compiler_detected_ver_list']=r['version_lst']
             misc['compiler_detected_ver_str']=cver
             misc['compiler_detected_ver_raw']=r['version_raw']

             if o=='con':
                ck.out(sep)
                ck.out('Detected compiler version: '+cver)
                ck.out('')

       if sa=='compile':
          # Check linking libs + include paths for all deps
          sll=''
          sin=''
          for k in deps:
              depsk=deps[k]
              kv=depsk.get('cus',{})

              pl1=kv.get('path_lib','')
              if pl1=='': pl1=kv.get('path_static_lib','')
              pl1d=kv.get('path_dynamic_lib','')
              if pl1d=='': pl1d=pl1

              # Check if extra
              extra_libs=depsk.get('extra_libs',[])
              els=[]

              cus_extra_libs=kv.get('extra_static_libs',{})
              if len(cus_extra_libs)==0: cus_extra_libs=kv.get('extra_dynamic_libs',{})

              for el in extra_libs:
                  x=cus_extra_libs.get(el,'')
                  if x=='':
                     return {'return':1, 'error':'library '+el+'is not defined in dependencies'}
                  els.append(x) 

              x=kv.get('static_lib','')
              if x=='' and ctype=='dynamic' and kv.get('dynamic_lib','')!='': x=kv['dynamic_lib']
              els.append(x)

              path_added=False
              for pl2 in els:
                  if pl2!='':
                     if sll!='': sll+=' '
                     if ctype=='dynamic' and (remote=='yes' or (pl1d!='' and wb!='yes')) and csd.get('customize',{}).get('can_strip_dynamic_lib','')=='yes':
                        pl2x=os.path.splitext(pl2)[0]
                        if pl2x.startswith('lib'): pl2x=pl2x[3:]
                        if not path_added:
                           sll+=' '+svarb+svarb1+'CK_FLAG_PREFIX_LIB_DIR'+svare1+svare+eifsc+pl1d+eifsc
                           path_added=True
                        sll+=' -l'+pl2x
                     else:
                        sll+=eifsc
                        if pl1!='': 
                           sll+=pl1+sdirs
                        sll+=pl2
                        sll+=eifsc

              pl3l=kv.get('path_include','')
              pl3ll=kv.get('path_includes',[])
              if pl3l not in pl3ll:
                 pl3ll.append(pl3l)

              for pl3 in pl3ll:
                  if pl3!='':
                     if sin!='': sin+=' '
                     sin+=svarb+svarb1+'CK_FLAG_PREFIX_INCLUDE'+svare1+svare+eifsc+pl3+eifsc

          # Check if local includes
          linc=meta.get('include_dirs',[])
          if len(linc)>0:
             for q in linc:
                 # Check if source from another entry (species)
                 full_path=''

                 if q.startswith('$#ck_take_from_{'):
                    r9=substitute_some_ck_keys({'string':q})
                    if r9['return']>0: return r9
                    x=r9['string']
                 else:
                    if td!='': full_path='..'+sdirs
                    else: full_path=''
                    x=os.path.join(full_path,q)

                 if x.endswith('\\'): x=x[:-1] # otherwise can be problems on Windows ...

                 if sin!='': sin+=' '
                 sin+=svarb+svarb1+'CK_FLAG_PREFIX_INCLUDE'+svare1+svare+eifsc+x+eifsc

          # Check if includes as environment var (we search in env settings, 
          #    not in real env, otherwise, can have problems, when concatenating -I with empty string)
          line=meta.get('compiler_add_include_as_env_from_deps',[])
          if len(line)>0:
             for q in line:
                 for g1 in deps:
                     gg=deps[g1]
                     gge=gg.get('dict',{}).get('env',{})
                     xgge=gge.get(q,'')
                     if xgge!='':
                        if sin!='': sin+=' '
                        sin+=svarb+svarb1+'CK_FLAG_PREFIX_INCLUDE'+svare1+svare+eifsc+xgge+eifsc

          # Obtaining compile CMD (first from program entry, then default from this module)
          ccmds=meta.get('compile_cmds',{})
          ccmd=ccmds.get(hplat,{})
          if len(ccmd)==0:
             ccmd=ccmds.get('default',{})
          if len(ccmd)==0:
             ccmds=cfg.get('compile_cmds',{})
             ccmd=ccmds.get(hplat,{})
             if len(ccmd)==0:
                ccmd=ccmds.get('default',{})

          sccmd=ccmd.get('cmd','')
          if sccmd=='':
             return {'return':1, 'error':'compile CMD is not found'}

          sccmd=sccmd.replace('$#script_ext#$',sext)

          # Source files
          sfs=meta.get('source_files',[])

          compiler_env=meta.get('compiler_env','')
          if compiler_env=='': compiler_env='CK_CC'

          sfprefix='..'+sdirs

          scfb=''

          flags_def=''
          if fspeed=='yes':
               scfb+=' '+svarb+'CK_OPT_SPEED'+svare+' '
               flags_def+=' '+svarb+'CK_OPT_SPEED'+svare+' '
          elif fsize=='yes':
               flags_def+=' '+svarb+'CK_OPT_SIZE'+svare+' '

          scfb+=svarb+'CK_FLAGS_CREATE_OBJ'+svare
          scfb+=' '+svarb+'CK_COMPILER_FLAGS_OBLIGATORY'+svare
          if ctype=='dynamic':
             scfb+=' '+svarb+'CK_FLAGS_DYNAMIC_BIN'+svare
          elif ctype=='static':
             scfb+=' '+svarb+'CK_FLAGS_STATIC_BIN'+svare
          scfb+=' '+svarb+svarb1+'CK_FLAG_PREFIX_INCLUDE'+svare1+svare+sfprefix

          scfa=''

          # Check build -D flags
          sbcv=''
          bcv=meta.get('build_compiler_vars',{})

          for q in rcv:
              if q in bcv: del(bcv[q])

          bcv.update(cv)

          # Update env if energy meter
          if me=='yes':
             bcv['CK_MONITOR_ENERGY']='1'

          if o=='con' and len(bcv)>0:
             ck.out(sep)
             ck.out('Compiler vars:')

          for k in bcv:
              kv=bcv[k]

              if sbcv!='': sbcv+=' '
              sbcv+=svarb+svarb1+'CK_FLAG_PREFIX_VAR'+svare1+svare+k
              if kv!='': sbcv+='='+str(kv)

              if o=='con':
                 ck.out('  '+k+'='+str(kv))

          # Check if compiler flags as environment variable
          cfev=meta.get('compiler_flags_as_env','')
          if cfev!='':
             cfev=cfev.replace('$<<',svarb).replace('>>$',svare)
             sbcv+=' '+cfev

          # Prepare compilation
          sb+='\n'

          denv=dcomp.get('env',{})
          sobje=denv.get('CK_OBJ_EXT','')
          sofs=''
          xsofs=[]

          if ee!='':
             sb+='\n'+no+ee+'\n\n'

          if o=='con': ck.out(sep)

          # Compilation flags
          xcfb=scfb

          if sbcv!='': xcfb+=' '+sbcv
          if sin!='': xcfb+=' '+sin
          xcfb+=' '+flags

          # Linking flags
          slfb=svarb+'CK_COMPILER_FLAGS_OBLIGATORY'+svare
          slfb+=' '+lflags
          if ctype=='dynamic':
             slfb+=' '+svarb+'CK_FLAGS_DYNAMIC_BIN'+svare
          elif ctype=='static':
             slfb+=' '+svarb+'CK_FLAGS_STATIC_BIN'+svare

          slfa=' '+svarb+svarb1+'CK_FLAGS_OUTPUT'+svare1+svare+target_exe
          slfa+=' '+svarb+'CK_LD_FLAGS_MISC'+svare
          slfa+=' '+svarb+'CK_LD_FLAGS_EXTRA'+svare

          if sll!='': slfa+=' '+sll

          evr=meta.get('extra_ld_vars','')
          if evr!='':
             evr=evr.replace('$<<',svarb).replace('>>$',svare)
             slfa+=' '+evr

          # Check if includes as environment var
          llinkle=meta.get('linker_add_lib_as_env',[])
          if len(llinkle)>0:
             for q in llinkle:
                 if slfa!='': slfa+=' '
                 slfa+=svarb+svarb1+q+svare1+svare

          # Check if call compile CMD only once with all files
          if meta.get('use_compile_script','')=='yes':
             cc=sccmd

             # Add compiler and linker flags as environment
             sb+='\n'
             genv={'CK_PROG_COMPILER_FLAGS_BEFORE':xcfb,
                   'CK_PROG_LINKER_FLAGS_BEFORE':slfb,
                   'CK_PROG_LINKER_FLAGS_AFTER':slfa,
                   'CK_PROG_COMPILER_VARS':sbcv,
                   'CK_PROG_COMPILER_FLAGS':flags_def+' '+flags,
                   'CK_PROG_LINKER_LIBS':sll,
                   'CK_PROG_TARGET_EXE':target_exe}

             extcomp=meta.get('extra_env_for_compilation',{})
             if len(extcomp)>0:
                genv.update(extcomp)

             if len(eefc)>0:
                genv.update(eefc)

             for gg in genv:
                 gx=genv[gg]
                 if eifs!='': gx=gx.replace(eifs, '\\'+eifs)
                 sb+=no+eset+' '+gg+'='+eifs+gx+eifs+'\n'

             sb+='echo '+eifs+cc+eifs+'\n'
             sb+=no+cc+'\n'
             sb+=no+sqie+'\n'

             sb+='\n'
          else:
             for sf in sfs:
                 sf=sf.strip()

                 xcfa=scfa

                 # Check if source from another entry (species)
                 full_path=''
                 if sf.startswith('$#ck_take_from_{'):
                    b2=sf.find('}#$')
                    if b2=='':
                       return {'return':1, 'error':'can\'t parse source file '+sf+' ...'}
                    bb=sf[16:b2]

                    rb=ck.access({'action':'load',
                                  'module_uoa':muoa,
                                  'data_uoa':bb})
                    if rb['return']>0: 
                       return {'return':1, 'error':'can\'t find sub-entry '+bb}

                    sf=sf[b2+3:]

                    full_path=rb['path']
                 else:
                    full_path=sfprefix

                 sf0,sf1=os.path.splitext(sf)

                 sf00=os.path.basename(sf)
                 sf00a,sf00b=os.path.splitext(sf00)

                 sfobj=sf00a+sobje
                 if sofs!='': sofs+=' '
                 sofs+=sfobj
                 xsofs.append(sfobj)

                 if 'CK_FLAGS_OUTPUT' in denv:
                    xcfa+=' '+svarb+svarb1+'CK_FLAGS_OUTPUT'+svare1+svare+sfobj

                 cc=sccmd
                 cc=cc.replace('$#source_file#$', os.path.join(full_path,sf))

                 cc=cc.replace('$#compiler#$', svarb+compiler_env+svare)

                 cc=cc.replace('$#flags_before#$', xcfb)
                 cc=cc.replace('$#flags_after#$', xcfa)

                 if sunparsed!='': cc+=' '+sunparsed

                 sb+='echo '+eifs+cc+eifs+'\n'
                 sb+=no+cc+'\n'
                 sb+=no+sqie+'\n'

                 sb+='\n'

          # Obtaining link CMD (first from program entry, then default from this module)
          if sofs!='':
             linker_env=meta.get('linker_env','')
             if linker_env=='': linker_env=compiler_env

             lcmds=meta.get('link_cmds',{})
             lcmd=lcmds.get(hplat,{})
             if len(lcmd)==0:
                lcmd=lcmds.get('default',{})
             if len(lcmd)==0:
                lcmds=cfg.get('link_cmds',{})
                lcmd=lcmds.get(hplat,{})
                if len(lcmd)==0:
                   lcmd=lcmds.get('default',{})

             slcmd=lcmd.get('cmd','')
             if slcmd!='':
                slfb=svarb+'CK_COMPILER_FLAGS_OBLIGATORY'+svare
                slfb+=' '+lflags
                if ctype=='dynamic':
                   slfb+=' '+svarb+'CK_FLAGS_DYNAMIC_BIN'+svare
                elif ctype=='static':
                   slfb+=' '+svarb+'CK_FLAGS_STATIC_BIN'+svare

                slfa=' '+svarb+svarb1+'CK_FLAGS_OUTPUT'+svare1+svare+target_exe
                slfa+=' '+svarb+'CK_LD_FLAGS_MISC'+svare
                slfa+=' '+svarb+'CK_LD_FLAGS_EXTRA'+svare

                if sll!='': slfa+=' '+sll

                evr=meta.get('extra_ld_vars','')
                if evr!='':
                   evr=evr.replace('$<<',svarb).replace('>>$',svare)
                   slfa+=' '+evr

                # Check if includes as environment var
                llinkle=meta.get('linker_add_lib_as_env',[])
                if len(llinkle)>0:
                   for q in llinkle:
                       if slfa!='': slfa+=' '
                       slfa+=svarb+svarb1+q+svare1+svare

                cc=slcmd
                cc=cc.replace('$#linker#$', svarb+linker_env+svare)
                cc=cc.replace('$#obj_files#$', sofs)
                cc=cc.replace('$#flags_before#$', slfb)
                cc=cc.replace('$#flags_after#$', slfa)

                sb+='echo '+eifs+cc+eifs+'\n'
                sb+=no+cc+'\n'
                sb+=no+sqie+'\n'

          # Add objdump
          sb+='\n'+no+svarb+'CK_OBJDUMP'+svare+' '+target_exe+' '+stro+' '+target_exe+'.dump'+'\n'

          # Add md5sum
          x='<'
          if hplat=='win':x='' 
          sb+='\n'+no+md5sum+' '+x+' '+target_exe+'.dump '+stro+' '+target_exe+'.md5'+'\n'

          # Add git hash (if supported)
          sb+='\n'+no+'git rev-parse HEAD '+stro+' '+target_exe+'.git_hash'+'\n'

          # Stop energy monitor, if needed and if supported
          if me=='yes' and sspm2!='':
             if o=='con':
                ck.out('')
                ck.out('Adding energy monitor')
                ck.out('')

             sb+='\n'
             sb+=scall+' '+sspm2+'\n'
             sb+='\n'

          # Add exit /0 if needed (on Windows git and md5sum can mess up return code)
          if bex!='':
             sb+='\n\n'+bex.replace('$#return_code#$','0')

          # Record to tmp batch and run
          rx=ck.gen_tmp_file({'prefix':'tmp-', 'suffix':sext, 'remove_dir':'yes'})
          if rx['return']>0: return rx
          fn=rx['file_name']

          rx=ck.save_text_file({'text_file':fn, 'string':sb})
          if rx['return']>0: return rx

          y=''
          if sexe!='':
             y+=sexe+' '+sbp+fn+envsep
          y+=' '+scall+' '+sbp+fn

          if o=='con':
             ck.out('')
             ck.out('Executing prepared batch file '+fn+' ...')

          sys.stdout.flush()
          start_time1=time.time()

          if ubtr!='': y=ubtr.replace('$#cmd#$',y)

          ############################################## Compiling code here ##############################################
          rx=0
          ry=ck.system_with_timeout({'cmd':y, 'timeout':xcto})
          rry=ry['return']

          if rry>0:
             if rry!=8: return ry
          else:
             rx=ry['return_code']

          comp_time=time.time()-start_time1
          ccc['compilation_time']=comp_time

          if sca!='yes':
             if fn!='' and os.path.isfile(fn): os.remove(fn)

          git_hash=''
          # Try to read git hush file
          if os.path.isfile(target_exe+'.git_hash'):
             rz=ck.load_text_file({'text_file':target_exe+'.git_hash'})
             if rz['return']==0:
                git_hash=rz['string'].strip()
                ccc['program_git_hash']=git_hash

          ofs=0
          md5=''
          if rry==8:
             misc['compilation_success']='no'
             misc['compilation_success_bool']=False
             misc['fail_reason']=ry['error']

             ccc['compilation_success']='no'
             ccc['compilation_success_bool']=False
             ccc['fail_reason']=ry['error']
          elif rx>0:
             misc['compilation_success']='no'
             misc['compilation_success_bool']=False
             misc['fail_reason']='return code '+str(rx)+' !=0 '

             ccc['compilation_success']='no'
             ccc['compilation_success_bool']=False
             ccc['fail_reason']='return code '+str(rx)+' !=0 '
          else:
             misc['compilation_success']='yes'
             misc['compilation_success_bool']=True
             ccc['compilation_success']='yes'
             ccc['compilation_success_bool']=True

             # Check some characteristics
             if os.path.isfile(target_exe):
                ccc['binary_size']=os.path.getsize(target_exe)
                ofs=ccc['binary_size']

                # Try to read md5 file
                if os.path.isfile(target_exe+'.md5'):
                   rz=ck.load_text_file({'text_file':target_exe+'.md5'})
                   if rz['return']==0:
                      md5x=rz['string']
                      ix=md5x.find(' ')
                      if ix>0:
                         md5=md5x[:ix].strip()
                         ccc['md5_sum']=md5

             # Check obj file sizes
             if len(xsofs)>0:
                ofs=0
                ccc['obj_sizes']={}
                for q in xsofs:
                    if os.path.isfile(q):
                       ofs1=os.path.getsize(q)
                       ccc['obj_sizes'][q]=ofs1
                       ofs+=ofs1
                ccc['obj_size']=ofs

          ccc['compilation_time_with_module']=time.time()-start_time

          if o=='con':
             ck.out(sep)
             ck.out('Compilation time: '+('%.3f'%comp_time)+' sec.; Object size: '+str(ofs)+'; MD5: '+md5)
             if misc.get('compilation_success','')=='no':
                ck.out('Warning: compilation failed!')

    ##################################################################################################################
    ################################### Run ######################################
    elif sa=='run':
       start_time=time.time()

       # Remote dir
       if remote=='yes':
          rdir=tosd.get('remote_dir','')
          if rdir!='' and not rdir.endswith(stdirs): rdir+=stdirs

       src_path_local=p+sdirs
       if remote=='yes':
          src_path=rdir+stdirs
       else:
          src_path=src_path_local

       sc=i.get('skip_calibration','')
       xcalibrate_time=i.get('calibration_time','')
       if xcalibrate_time=='': xcalibrate_time=cfg['calibration_time']
       calibrate_time=float(xcalibrate_time)

       # Update environment
       env1=meta.get('run_vars',{})
       for q in env1:
           if q not in env:
              x=env1[q]
              try:
                 x=x.replace('$#src_path#$', src_path)
              except Exception as e: # need to detect if not string (not to crash)
                 pass
              env[q]=x

       # Update env if repeat
       if sc!='yes' and 'CT_REPEAT_MAIN' in env1:
          if repeat!=-1:
             if 'CT_REPEAT_MAIN' not in env1:
                return {'return':1, 'error':'this program is not supporting execution time calibration'}
             env['CT_REPEAT_MAIN']=str(repeat) # it is fixed by user
             sc='yes'
          else:
             repeat=int(env1.get('CT_REPEAT_MAIN','1'))
             env['CT_REPEAT_MAIN']='$#repeat#$' # find later

       # Update env if energy meter
       if me=='yes':
          env['CK_MONITOR_ENERGY']='1'
          env['XOPENME_FILES']=svarb+svarb1+'CK_ENERGY_FILES'+svare1+svare

       # Check cmd key
       run_cmds=meta.get('run_cmds',{})
       if len(run_cmds)==0:
          return {'return':1, 'error':'no CMD for run'}

       krun_cmds=sorted(list(run_cmds.keys()))

       kcmd=i.get('cmd_key','')
       if kcmd=='':
          if len(krun_cmds)>1:
             ck.out('')
             ck.out('More than one commmand line is found to run this program:')
             ck.out('')
             zz={}
             iz=0
             for z in sorted(krun_cmds):
                 zcmd=run_cmds[z].get('run_time',{}).get('run_cmd_main','')

                 zs=str(iz)
                 zz[zs]=z

                 if zcmd!='': z+=' ('+zcmd+')'
                 ck.out(zs+') '+z)

                 iz+=1

             ck.out('')
             rx=ck.inp({'text':'Select command line (or Enter to select 0): '})
             x=rx['string'].strip()
             if x=='': x='0'

             if x not in zz:
                return {'return':1, 'error':'command line number is not recognized'}

             kcmd=zz[x]

          else:
             kcmd=krun_cmds[0]
       else:
          if kcmd not in krun_cmds:
             return {'return':1, 'error':'CMD key not found in program description'}

       # Command line key is set
       vcmd=run_cmds[kcmd]
       misc['cmd_key']=kcmd

       c=''

       rt=vcmd.get('run_time',{})

       rif=rt.get('run_input_files',[])
       rifo={}

       # Check if dynamic and remote to copy .so to devices (but for the 1st autotuning and statistical iteration!)
       if ctype=='dynamic' and remote=='yes':
          if srn==0 and ati==0:
             for q in deps:
                 qq=deps[q].get('cus','')
                 qdl=qq.get('dynamic_lib','')
                 if qdl!='' and qq.get('skip_copy_to_remote','')!='yes':
                    qpl=qq.get('path_lib','')
                    qq1=os.path.join(qpl,qdl)
                    rif.append(qq1)
                    rifo[qq1]='yes' # if pushing to external, do not use current path

       # Check if run_time env is also defined
       rte=rt.get('run_set_env2',{})
       if len(rte)>0:
          env.update(rte)

       # Add compiler dep again, if there (otherwise some libs can set another compiler)
       x=deps.get('compiler',{}).get('bat','')
       if remote!='yes' and x!='' and not sb.endswith(x):
          sb+='\n'+no+x.strip()+' 1\n' # We set 1 to tell environment that it should set again even if it was set before

       # Add env
       sb+='\n'
       for k in sorted(env):
           v=str(env[k])

           if eifs!='' and wb!='yes':
              if v.find(' ')>=0 and not v.startswith(eifs):
                 v=eifs+v+eifs

           sb+=no+etset+' '+k+'='+str(v)+'\n'
       sb+='\n'

       if tosd.get('extra_env','')!='':
          sb+=no+tosd['extra_env']+'\n'

       # Command line preparation
       c=rt.get('run_cmd_main','')
       if c=='':
          return {'return':1, 'error':'cmd is not defined'}
       c=c.replace('$<<',svarb+svarb1).replace('>>$',svare1+svare)

       # Add extra before CMD if there ...
       c=prcmd+' '+c

       # Replace bin file
       te=target_exe
       if meta.get('skip_add_prefix_for_target_file','')!='yes':
          te=stbp+te

       # Check if affinity
       if aff!='':
          te=aff+' '+te

       c=c.replace('$#BIN_FILE#$', te)
       c=c.replace('$#os_dir_separator#$', stdirs)
       c=c.replace('$#src_path#$', src_path)

       c=c.replace('$#env1#$',svarb)
       c=c.replace('$#env2#$',svare)

       if ercmd!='':
          c+=' '+ercmd

       # Update keys in run cmd (useful for CMD autotuning)
       for k in rcsub:
           xv=rcsub[k]
           c=c.replace('$#'+k+'#$',str(xv))

       # Check if takes datasets from CK
       dtags=vcmd.get('dataset_tags',[])
       dmuoa=cfg['module_deps']['dataset']
       dduoa=i.get('dataset_uoa','')
       if dduoa!='' or len(dtags)>0:
          if dduoa=='':
             misc['dataset_tags']=dtags

             tags=''
             for q in dtags:
                 if tags!='': tags+=','
                 tags+=q

             rx=ck.access({'action':'search',
                           'module_uoa':dmuoa,
                           'tags':tags})
             if rx['return']>0: return rx

             lst=rx['lst']

             if len(lst)==0:
                return {'return':1, 'error':'no related datasets found (tags='+tags+')'}  
             elif len(lst)==1:
                dduoa=lst[0].get('data_uid','')
             else:
                ck.out('')
                ck.out('More than one dataset entry is found for this program:')
                ck.out('')
                zz={}
                iz=0
                for z1 in sorted(lst, key=lambda v: v['data_uoa']):
                    z=z1['data_uid']
                    zu=z1['data_uoa']

                    zs=str(iz)
                    zz[zs]=z

                    ck.out(zs+') '+zu+' ('+z+')')

                    iz+=1

                ck.out('')
                rx=ck.inp({'text':'Select dataset UOA (or Enter to select 0): '})
                x=rx['string'].strip()
                if x=='': x='0'

                if x not in zz:
                   return {'return':1, 'error':'dataset number is not recognized'}

                dduoa=zz[x]

          if dduoa=='':
             return {'return':1, 'error':'dataset is not specified'}  

       misc['dataset_uoa']=dduoa

       # If remote
       if remote=='yes':
          if target_exe=='':
             return {'return':1, 'error':'currently can\'t run benchmarks without defined executable on remote platform'}

          rs=tosd['remote_shell'].replace('$#device#$',xtdid)
          rse=tosd.get('remote_shell_end','')+' '

          if sdi!='yes':
             ck.out(sep)
             r=ck.access({'action':'init_device',
                          'module_uoa':cfg['module_deps']['platform'],
                          'os_dict':tosd,
                          'device_id':tdid,
                          'out':o})
             if r['return']>0: return r

          if srn==0:
             # Copy exe
             y=tosd.get('remote_push_pre','').replace('$#device#$',xtdid)
             if y!='':
                y=y.replace('$#file1#$', target_exe)
                y=y.replace('$#file1s#$', target_exe)
                y=y.replace('$#file2#$', rdir+target_exe)

                if o=='con':
                   ck.out(sep)
                   ck.out(y)
                   ck.out('')

                ry=os.system(y)
                if ry>0:
                   return {'return':1, 'error':'copying to remote device failed'}

             y=tosd['remote_push'].replace('$#device#$',xtdid)
             y=y.replace('$#file1#$', target_exe)
             y=y.replace('$#file1s#$', target_exe)
             y=y.replace('$#file2#$', rdir+target_exe)

             if o=='con':
                ck.out(sep)
                ck.out(y)
                ck.out('')

             ry=os.system(y)
             if ry>0:
                return {'return':1, 'error':'copying to remote device failed'}

             # Set chmod
             se=tosd.get('set_executable','')
             if se!='':
                y=rs+' '+se+' '+rdir+target_exe+' '+rse
                if o=='con':
                   ck.out(sep)
                   ck.out(y)
                   ck.out('')

                ry=os.system(y)
                if ry>0:
                   return {'return':1, 'error':'making binary executable failed on remote device'}

          if sdi!='yes' and srn==0 or ati==0:
             # Copy explicit input files, if first time
             for df in rif:
                 df0, df1 = os.path.split(df)

                 # Push data files to device
                 y=tosd.get('remote_push_pre','').replace('$#device#$',xtdid)

                 if df in rifo:
                    dfx=df
                    dfy=rdir+stdirs+df1
                 else:
                    dfx=os.path.join(p,df)
                    dfy=rdir+stdirs+df

                 if y!='':
                    y=y.replace('$#file1#$', dfx)
                    y=y.replace('$#file1s#$', df1)
                    y=y.replace('$#file2#$', dfy)

                    if o=='con':
                       ck.out(sep)
                       ck.out(y)
                       ck.out('')

                    ry=os.system(y)
                    if ry>0:
                       return {'return':1, 'error':'copying to remote device failed'}

                 y=tosd['remote_push'].replace('$#device#$',xtdid)
                 y=y.replace('$#file1#$', dfx)
                 y=y.replace('$#file1s#$', df1)
                 y=y.replace('$#file2#$', dfy)
                 if o=='con':
                    ck.out(sep)
                    ck.out(y)
                    ck.out('')

                 ry=os.system(y)
                 if ry>0:
                    return {'return':1, 'error':'copying to remote device failed'}

       # Loading dataset
       dp=''
       if dduoa!='':
          rx=ck.access({'action':'load',
                        'module_uoa':dmuoa,
                        'data_uoa':dduoa})
          if rx['return']>0: return rx
          dd=rx['dict']
          dp=rx['path']

          if remote=='yes':
             c=c.replace('$#dataset_path#$','')
          else:
             c=c.replace('$#dataset_path#$',dp+sdirs)

          dfiles=dd.get('dataset_files',[])
          if len(dfiles)>0:

             dfile=i.get('dataset_file','')
             if dfile!='':
                dfiles=[dfile]
                misc['dataset_file']=dfile
             elif len(dfiles)>0:
                if len(dfiles)==1:
                   dfile=dfiles[0]
                else:
                   ck.out('************ Selecting dataset file ...')
                   ck.out('')
                   r=ck.access({'action':'select_list',
                                'module_uoa':cfg['module_deps']['choice'],
                                'choices':dfiles,
                                'desc':dfiles})
                   if r['return']>0: return r
                   dfile=r['choice']

             for k in range(0, len(dfiles)):
                 df=dfiles[k]
                 if dfile!='' and k==0: df=dfile
                 kk='$#dataset_filename'
                 if k>0: kk+='_'+str(k)
                 kk+='#$'
                 c=c.replace(kk, df)

                 if remote=='yes' and srn==0 and sdi!='yes' and sdc!='yes':
                    # check if also extra files
                    dfx=[df]

                    dfx1=dd.get('extra_dataset_files',{}).get(df,[])
                    for dfy in dfx1:
                        if dfy not in dfx:
                           dfx.append(dfy)

                    for dfz in dfx:
                        df0, df1 = os.path.split(dfz)

                        # Push data files to device
                        y=tosd.get('remote_push_pre','').replace('$#device#$',xtdid)
                        if y!='':
                           y=y.replace('$#file1#$', os.path.join(dp,dfz))
                           y=y.replace('$#file1s#$', df1)
                           y=y.replace('$#file2#$', rdir+stdirs+dfz)

                           if o=='con':
                              ck.out(sep)
                              ck.out(y)
                              ck.out('')

                           ry=os.system(y)
                           if ry>0:
                              return {'return':1, 'error':'copying to remote device failed'}

                        # Push data files to device, if first time
                        y=tosd['remote_push'].replace('$#device#$',xtdid)
                        y=y.replace('$#file1#$', os.path.join(dp,dfz))
                        y=y.replace('$#file1s#$', df1)
                        y=y.replace('$#file2#$', rdir+stdirs+dfz)
                        if o=='con':
                           ck.out(sep)
                           ck.out(y)
                           ck.out('')

                        ry=os.system(y)
                        if ry>0:
                           return {'return':1, 'error':'copying to remote device failed'}

          rcm=dd.get('cm_properties',{}).get('run_time',{}).get('run_cmd_main',{})
          for k in rcm:
              kv=rcm[k]
              c=c.replace('$#'+k+'#$',kv)

          misc['dataset_uoa']=dduoa

       # Check if has unparsed
       if sunparsed!='':
          c+=' '+sunparsed

       # Check if redirect output
       rco1=rt.get('run_cmd_out1','')
       rco2=rt.get('run_cmd_out2','')

       if ee!='':
          sb+='\n'+no+ee+'\n\n'

       sb+='\necho executing\n'

       if remote!='yes' and cons!='yes':
          if rco1!='': c+=' '+stro+' '+rco1
          if rco2!='': c+=' '+stre+' '+rco2
       sb+=no+c+'\n'

       # Stop energy monitor, if needed and if supported
       if me=='yes' and sspm2!='':
          if o=='con':
             ck.out('')
             ck.out('Adding energy monitor')
             ck.out('')

          sb+='\n'
          sb+=scall+' '+sspm2+'\n'
          sb+='\n'

       fn=''

       # Check post-processing scripts
       lppc=rt.get('post_process_cmds',[])
       ppc=rt.get('post_process_cmd','')
       if ppc!='': lppc.append(ppc)

       fgtf=rt.get('fine_grain_timer_file','')

       # Check if extra post_process
       if eppc!='':
          sb+=eppc+'\n'

       sb=sb.replace('$#BIN_FILE#$', te)

       te1=te
       if te.startswith('./'):
          te1=te[2:]
       sb=sb.replace('$#ONLY_BIN_FILE#$', te1)

       # Calibrate execution time (to make it longer and minimize system variation, 
       #   if supported)
       csb=sb
       orepeat=repeat
       calibrate_success=False

       xcn_max=i.get('calibration_max','')
       if xcn_max=='': xcn_max=cfg['calibration_max']
       cn_max=int(xcn_max)


       for g in rt.get('run_output_files',[]):
           rof.append(g)

       cn=1
       while True:
          # Clean output files
          rofx=[]
          if rco1!='': rofx.append(rco1)
          if rco2!='': rofx.append(rco2)
          for df in rof:
              rofx.append(df)

          if o=='con' and len(rofx)>0:
             ck.out('  Cleaning output files:')

          for df in rofx:
              if o=='con': ck.out('    '+df)

              if remote=='yes':
                 # Clean data files on device
                 y=rs+' '+tosd['delete_file']+ ' '+rdir+stdirs+df+' '+rse
                 if o=='con':
                    ck.out('')
                    ck.out(y)
                    ck.out('')

                 ry=os.system(y)

                 if tosd.get('delete_file_extra','')!='':
                    y=tosd['delete_file_extra']+df+' '+rse
                    if o=='con':
                       ck.out('')
                       ck.out(y)
                       ck.out('')

                    ry=os.system(y)

              if os.path.isfile(df): 
                 os.remove(df)

          if o=='con': ck.out('')

          if sc!='yes' and 'CT_REPEAT_MAIN' in env1:
             if o=='con':
                ck.out(sep)
                ck.out('### Calibration '+str(cn)+' out of '+xcn_max+' ; Kernel repeat number = '+str(repeat))

          sb=csb
          if sc!='yes' and 'CT_REPEAT_MAIN' in env1 and repeat!=-1:
             sb=sb.replace('$#repeat#$', str(repeat))

          # Check sudo init
          if isd=='yes':
             if o=='con': 
                ck.out(sep)
                ck.out('  (preparing sudo - may ask password ...)')
             if remote!='yes':
                os.system(sudo_init)

          if o=='con':  ck.out(sep)

          # Prepare execution
          if remote=='yes':
             # Prepare command as one line
             y=''

             if isd=='yes': 
                y+=sudo_init+' '+envtsep
                y+=sudo_pre+' '

             x=sb.split('\n')
             for q in x:
                 if q!='':
                    if y!='': y+=envtsep
                    y+=' '+q

             if isd=='yes': y=y+' '+envtsep+' '+sudo_post

             if eifsx!='': y=y.replace('"','\\"')
             y=rs+' '+eifsx+tosd['change_dir']+' '+rdir+envtsep+' '+y+eifsx+' '+rse

             if cons!='yes':
                if rco1!='': y+=' '+stro+' '+rco1
                if rco2!='': y+=' '+stre+' '+rco2

             if o=='con':
                ck.out(y)

          else:
             # Record to tmp batch and run
             rx=ck.gen_tmp_file({'prefix':'tmp-', 'suffix':sext, 'remove_dir':'yes'})
             if rx['return']>0: return rx
             fn=rx['file_name']

             sb=bbp+'\n\n'+sb

             rx=ck.save_text_file({'text_file':fn, 'string':sb})
             if rx['return']>0: return rx

             y=''
             if sexe!='':
                y+=sexe+' '+sbp+fn+envsep

             if isd=='yes':
                yy=sudo_pre+' '+sbp+fn+' '+envtsep+' '+sudo_post
             else:
                yy=scall+' '+sbp+fn
             y+=' '+yy

             if o=='con':
                ck.out('Prepared script:')
                ck.out('')
                ck.out(sb)
                ck.out(sep)
                ck.out('  ('+y.strip()+')')

          if remote!='yes' and ubtr!='': y=ubtr.replace('$#cmd#$',y)

          if o=='con':
             ck.out('')
             ck.out('  (sleep 0.5 sec ...)')
             time.sleep(0.5)
             ck.out('')
             ck.out('  (run ...)')

          ############################################## Running code here ##############################################
          sys.stdout.flush()
          start_time1=time.time()

          rx=0
          ry=ck.system_with_timeout({'cmd':y, 'timeout':xrto})
          rry=ry['return']
          if rry>0:
             if rry!=8: return ry
          else:
             rx=ry['return_code']

          exec_time=time.time()-start_time1

          if sca!='yes':
             if fn!='' and os.path.isfile(fn): os.remove(fn)

          # Pull files from the device if remote
          if remote=='yes':
             rof=rt.get('run_output_files',[])

             xrof=rof
             if i.get('pull_only_timer_files','')=='yes':
                xrof=[fgtf]

             for df in xrof:
                 # Pull output files from device
                 df0, df1 = os.path.split(df)

                 # Push data files to device
                 y=tosd['remote_pull'].replace('$#device#$',xtdid)
                 y=y.replace('$#file1#$', rdir+stdirs+df)
                 y=y.replace('$#file1s#$', df1)
                 y=y.replace('$#file2#$', df)
                 if o=='con':
                    ck.out('')
                    ck.out(y)
                    ck.out('')

                 ry=os.system(y)

                 y=tosd.get('remote_pull_post','').replace('$#device#$',xtdid)
                 if y!='':
                    y=y.replace('$#file1#$', rdir+stdirs+df)
                    y=y.replace('$#file1s#$', df1)
                    y=y.replace('$#file2#$', df)

                    if o=='con':
                       ck.out(sep)
                       ck.out(y)
                       ck.out('')

                    ry=os.system(y)
                    if ry>0:
                       return {'return':1, 'error':'pulling from remote device failed'}

          # Check if post-processing script from CMD
          if pp_uoa!='':
             if o=='con':
                ck.out('')
                ck.out('  (post processing from script ('+pp_uoa+' / '+pp_name+')..."')
                ck.out('')

             iz={'action':'run',
                 'module_uoa':cfg['module_deps']['script'],
                 'data_uoa':pp_uoa,
                 'name':pp_name,
                 'params':pp_params}
             rz=ck.access(iz)
             if rz['return']>0: return rz
             # For now ignore output

          # Check if post-processing script
          srx=0 # script exit code
          if len(lppc)>0:
             for ppc in lppc:
                 ppc=ppc.replace('$#src_path_local#$', src_path_local).replace('$#src_path#$', src_path)

#                Post-processing is performed on the local machine, so dataset path should be local, not remote!
#                 if remote=='yes':
#                    ppc=ppc.replace('$#dataset_path#$','')
#                 elif dp!='':
                 ppc=ppc.replace('$#dataset_path#$',dp+sdirs)

                 r9=substitute_some_ck_keys({'string':ppc})
                 if r9['return']>0: return r9
                 ppc=r9['string']

                 if o=='con':
                    ck.out('')
                    ck.out('  (post processing: "'+ppc+'"')
                    ck.out('')

                 srx=os.system(ppc)
                 # If error code > 0, set as the error code of the main program and quit
                 if srx>0:
                    if o=='con':
                       ck.out('  (post processing script failed!)')
                    break

          # If script failed, exit
          if srx>0: break

          # Check if fine-grain time
          if fgtf!='':
             if o=='con':
                ck.out('')
                ck.out('  (reading fine grain timers from '+fgtf+' ...)')
                ck.out('')

             rq=ck.load_json_file({'json_file':fgtf})
             if rq['return']>0: return rq
             drq=rq['dict']
             ccc.update(drq)
             et=drq.get('execution_time','')
             exec_time=0.0
             if et!='':
                exec_time=float(et)

             if o=='con':
                import json
                ck.out(json.dumps(drq, indent=2, sort_keys=True))
                ck.out('')

          # If return code >0 and program does not ignore return code, quit
          if (rx>0 and vcmd.get('ignore_return_code','').lower()!='yes') or rry>0:
             break

          # Check calibration
          if sc=='yes' or repeat==-1 or 'CT_REPEAT_MAIN' not in env1:
             calibrate_success=True
             break

          orepeat=repeat
          if exec_time<0.5: repeat*=10
          elif 0.8<(calibrate_time/exec_time)<1.4: 
             calibrate_success=True
             break
          else: 
             repeat*=float(calibrate_time/exec_time)
             if repeat<1: repeat=1
          repeat=int(repeat)

          if repeat==orepeat:
             calibrate_success=True
             break

          if o=='con' and sc!='yes':
             ck.out('')
             ck.out('### Calibration: time='+str(exec_time)+'; CT_REPEAT_MAIN='+str(orepeat)+'; new CT_REPEAT_MAIN='+str(repeat))

          if cn>=cn_max:
             return {'return':1, 'error':'calibration failed'}

          cn+=1

       if sc!='yes' and repeat!=-1 and 'CT_REPEAT_MAIN' in env1:
          if calibrate_success==False:
             return {'return':1, 'error':'calibration problem'}

       xrepeat=repeat
       if xrepeat<1: xrepeat=1

       ccc['return_code']=rx
       ccc['execution_time']=exec_time/repeat
       ccc['total_execution_time']=exec_time
       ccc['repeat']=xrepeat
       misc['calibration_success']=calibrate_success

       if rry==8:
          misc['run_success']='no'
          misc['run_success_bool']=False
          misc['fail_reason']=ry['error']

          ccc['run_success']='no'
          ccc['run_success_bool']=False
          ccc['fail_reason']=ry['error']
       if rx>0 and vcmd.get('ignore_return_code','').lower()!='yes':
          misc['run_success']='no'
          misc['run_success_bool']=False
          misc['fail_reason']='return code '+str(rx)+' !=0 '

          ccc['run_success']='no'
          ccc['run_success_bool']=False
          ccc['fail_reason']='return code '+str(rx)+' !=0 '
       else:
          misc['run_success']='yes'
          misc['run_success_bool']=True
          ccc['run_success']='yes'
          ccc['run_success_bool']=True

       ccc['execution_time_with_module']=time.time()-start_time

       if o=='con':
          ck.out('')
          x='Execution time: '+('%.3f'%exec_time)+' sec.'
          if repeat>1:
             x+='; Repetitions: '+str(repeat)+'; Normalized execution time: '+('%.9f'%(exec_time/repeat))+' sec.'
          ck.out(x)

    # Check to clean random directory
    #if grtd=='yes' and sca!='yes':
    #   os.chdir(odir)
    #   try:
    #      shutil.rmtree(cdir, ignore_errors=True)
    #   except Exception as e:
    #      pass

    return {'return':0, 'tmp_dir':rcdir, 'misc':misc, 'characteristics':ccc, 'deps':deps}

##############################################################################
# clean program work and tmp files

def clean(i):
    """
    Input:  {
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    i['sub_action']='clean'
    return process(i)

##############################################################################
# compile program

def compile(i):
    """
    Input:  {
               See "process_in_dir" (i.e. ck process_in_dir program --help)
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              Output of the last compile from function 'process_in_dir'
            }

    """

    i['sub_action']='compile'
    return process(i)

##############################################################################
# run program

def run(i):
    """
    Input:  {
               See "process_in_dir" (i.e. ck process_in_dir program --help)
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    i['sub_action']='run'
    return process(i)

##############################################################################
# prepare and run program pipeline (clean, compile, run, etc)

def pipeline(i):
    """
    Input:  {
              (repo_uoa)             - program repo UOA
              (module_uoa)           - program module UOA
              (data_uoa)             - program data UOA
                 or
              (program_uoa)          - useful if univeral pipeline is used, i.e. ck run pipeline:program program_uoa=...
                 or taken from .cm/meta.json from current directory

              (program_tags)         - select programs by these tags

              (program_dir)          - force program directory

              (host_os)              - host OS (detect, if omitted)
              (target_os)            - OS module to check (if omitted, analyze host)
              (device_id)            - device id if remote (such as adb)

              (local_platform)       - if 'yes', use host_os/target_os from the current platform
                                       (useful when replaying experiments from another machine and even OS)

              (prepare)              - if 'yes', only prepare setup, but do not clean/compile/run program
              (save_to_file)         - if !='', save updated input/output (state) to this file
              (skip_interaction)     - if 'yes' and out=='con', skip interaction to choose parameters

              (skip_device_init)     - if 'yes', skip device init
              (skip_info_collection) - if 'yes', skip info collection

                 Pipeline sections' settings:



              (no_platform_features)    - if 'yes', do not collect full platform features
              (no_dataset_features)     - if 'yes', do not search and extract data set features
              (no_clean)                - if 'yes', do not clean directory before compile/run
              (no_compile)              - if 'yes', do not compile program (useful when running the same program 
                                           under different system state conditions: CPU/GPU freq, cache/bus contentions, etc)
              (compile_only_once)       - if 'yes', compile only at first iteration
              (no_compiler_description) - if 'yes', do not search for most close compiler description with flags ...
              (no_run)                  - if 'yes', do not run program
                                             useful when using autotuning to find bugs in compiler, 
                                             or find differently generated code sequencies, etc ...
              (no_state_check)          - do not check system/CPU state (frequency) over iterations ...


              (generate_rnd_tmp_dir) - if 'yes', compile and run program in randomly generated temporal dir
                      or
              (tmp_dir)              - if !='', use this tmp_dir

              (skip_clean_after)     - if 'yes', do not remove run batch

              (console)              - if 'yes', output from program goes to console rather than file
                                          (usually for testing/demos)

              (cmd_key)              - CMD key
              (dataset_uoa)          - UOA of a dataset
              (dataset_file)         - dataset filename (if more than one inside one entry - suggest to have a UID in name)

              (compiler_env_uoa)     - env of a compiler  

              (compile_type)         - static or dynamic (dynamic by default;
                                         however takes compiler default_compile_type into account)
                  or
              (static or dynamic)

              (compiler_description_uoa)    - compiler description UOA (module compiler),
                                              if not set, there will be an attempt to detect the most close
                                              by version

              (compiler_vars)        - dict with set up compiler flags (-Dvar=value) -> 
                                       they will update the ones defined as default in program description ...

              (remove_compiler_vars) - list of compiler vars to remove

              (extra_env_for_compilation) - set environment variables before compiling program

              (flags)                - compile flags
              (lflags)               - link flags

              (compiler_flags)       - dict from compiler description (during autotuning),
                                       if set, description should exist in input:choices_desc#compiler_flags# ...

              (best_base_flag)       - if 'yes', try to select best flag if available ...
              (speed)                - the same as above

              (select_best_base_flag_for_first_iteration) - if 'yes' and autotuning_iteration=0


              (env)                  - preset environment
              (extra_env)            - extra environment as string
              (extra_run_cmd)        - extra CMD (can use $#key#$ for autotuning)
              (run_cmd_substitutes)  - dict with substs ($#key#$=value) in run CMD (useful for CMD autotuning)

              (sudo)                 - if 'yes', force using sudo 
                                       (otherwise, can use ${CK_SUDO_INIT}, ${CK_SUDO_PRE}, ${CK_SUDO_POST})

              (affinity)             - set processor affinity for tihs program run (if supported by OS - see "affinity" in OS)
                                       examples: 0 ; 0,1 ; 0-3 ; 4-7  (the last two can be useful for ARM big.LITTLE arhictecture

              (repeat)               - repeat kernel via environment CT_REPEAT_MAIN if supported
              (do_not_reuse_repeat)  - if 'yes', do not reuse repeat across iterations - needed for dataset exploration, for example
              (skip_calibration)     - if 'yes', skip execution time calibration (otherwise, make it around 4.0 sec)
              (calibration_time)     - calibration time in string, 4.0 sec. by default
              (calibration_max)      - max number of iterations for calibration, 10 by default

              (statistical_repetition_number) - current statistical repetition of experiment
                                                (for example, may be used to skip compilation, if >0)
              (autotuning_iteration)          - (int) current autotuning iteration (automatically updated during pipeline tuning)
              (the_same_dataset)              - if 'yes', the dataset stays the same across iterations 
                                                   so skip copying dataset to remote from 2nd iteration

              (repeat_compilation)   - if 'yes', force compilation, even if "statistical_repetition_number">0

              (cpu_freq)             - set CPU frequency, if supported (using SUDO, if also supported) 
                                         using script ck-set-cpu-online-and-frequency
                                       if "max" - try to set to maximum using script ck-set-cpu-performance
                                       if "min" - try to set to minimum using scrupt ck-set-cpu-powersave

              (gpu_freq)             - set GPU frequency, if supported (using SUDO, if also supported) 
                                         using script ck-set-gpu-online-and-frequency
                                       if "max" - try to set to maximum using script ck-set-gpu-performance
                                       if "min" - try to set to minimum using scrupt ck-set-gpu-powersave

              (energy)               - if 'yes', start energy monitoring (if supported) using script ck-set-power-sensors

              (gprof)                   - if 'yes', use gprof to collect profile info
              (perf)                    - if 'yes', use perf to collect hardware counters
              (vtune)                   - if 'yes', use Intel vtune to collect hardware counters

              (opencl_dvdt_profiler)    - if 'yes', attempt to use opencl_dvdt_profiler when running code ...

              (compile_timeout)         - (sec.) - kill compile job if too long
              (run_timeout)             - (sec.) - kill run job if too long

              (post_process_script_uoa) - run script from this UOA
              (post_process_subscript)  - subscript name
              (post_process_params)     - (string) add params to CMD


              (dependencies)         - compilation dependencies

              (choices)              - exposed choices (if any)
              (choices_order)        - vector of flattened choices (useful if optimizations need order 
                                        such as LLVM or using our GCC plugin iterface to reorder passes,
                                        since 'choices' dict does not have order)

              (features)             - exposed features (if any)

              (characteristics)      - measured characteristics/features/properties (if any)

              (state)                - kept across pipeline iterations (for example, during autotuning/exploration)

                                       (tmp_dir)    - if temporal directory is used, return it 
                                                      (useful if randomly generated, to be reused for run or further iterations)
                                       (repeat)     - kernel repeat ...
                                       (features.platform.cpu) - CPU features/properties obtained during iterations 
                                                                 to check that state didn't change ...
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              !!! The same as input, but with updated information !!!

              ready        - if 'yes', pipeline is ready (all obligatory choices are set)
                             if 'no', clean/compile/run program is postponed

              state        - should be preserved across autotuning, learning, exploration, validation iterations
            }

    """

    import os
    import json
    import sys

    o=i.get('out','')
    oo=''
    if o=='con': oo='con'

    pr=i.get('prepare','')
    si=i.get('skip_interaction','')

    if 'state' not in i: i['state']={}
    state=i['state']

    state['cur_dir']=os.getcwd()

    if 'choices' not in i: i['choices']={}
    choices=i['choices']

    if 'choices_desc' not in i: i['choices_desc']={}
    choices_desc=i['choices_desc']
    choices_order=i.get('choices_order',[])

    if 'features' not in i: i['features']={}
    features=i['features']

    if 'characteristics' not in i: i['characteristics']={}
    chars=i['characteristics']

    if 'dependencies' not in i: i['dependencies']={}
    cdeps=i['dependencies']

    ai=ck.get_from_dicts(i, 'autotuning_iteration', '', None)
    sbbf=ck.get_from_dicts(i, 'select_best_base_flag_for_first_iteration','', None)
    if sbbf=='yes' and ai!='' and ai==0:
       i['best_base_flag']='yes'

    i['ready']='no'
    i['fail']='no'

    ###############################################################################################################
    # PIPELINE SECTION: VARS INIT

    if o=='con':
       ck.out('Initializing universal program pipeline ...')
       ck.out('')

    muoa=work['self_module_uid']

    meta=ck.get_from_dicts(i, 'program_meta', {}, choices) # program meta if needed
    desc=ck.get_from_dicts(i, 'program_desc', {}, choices) # program desc if needed

    srn=ck.get_from_dicts(i, 'statistical_repetition_number', '', None)
    if srn=='': srn=0
    else: srn=int(srn)

    ati=ck.get_from_dicts(i, 'autotuning_iteration', '', None)
    if ati=='': ati=0
    else: ati=int(ati)

    ruoa=ck.get_from_dicts(i, 'repo_uoa', '', None)
    duoa=ck.get_from_dicts(i, 'data_uoa', '', choices)
    puoa=ck.get_from_dicts(i, 'program_uoa', '', None)
    if puoa!='': 
       duoa=puoa
       choices['data_uoa']=duoa
    ptags=ck.get_from_dicts(i, 'program_tags', '', choices)
    kcmd=ck.get_from_dicts(i, 'cmd_key', '', choices)
    dduoa=ck.get_from_dicts(i, 'dataset_uoa', '', choices)
    ddfile=ck.get_from_dicts(i, 'dataset_file', '', choices)
    druoa=ck.get_from_dicts(i, 'dataset_repo_uoa', '', None)

    ceuoa=ck.get_from_dicts(i, 'compiler_env_uoa', '', choices)

    scpuf=ck.get_from_dicts(i, 'cpu_freq', 'max', choices)
    sgpuf=ck.get_from_dicts(i, 'gpu_freq', 'max', choices)
    sme=ck.get_from_dicts(i, 'energy', '', choices)

    gprof=ck.get_from_dicts(i, 'gprof', '', choices)
    perf=ck.get_from_dicts(i, 'perf', '', choices)
    vtune=ck.get_from_dicts(i, 'vtune', '', choices)

    prcmd=''

    pdir=ck.get_from_dicts(i, 'program_dir', '', None) # Do not save, otherwise can't reproduce by other people
    if pdir!='': os.chdir(pdir)

    sdi=ck.get_from_dicts(i, 'skip_device_init', '', choices)
    sic=ck.get_from_dicts(i, 'skip_info_collection', '', choices)

    grtd=ck.get_from_dicts(i, 'generate_rnd_tmp_dir','', None)
    tdir=ck.get_from_dicts(i, 'tmp_dir','', None)
    sca=ck.get_from_dicts(i, 'skip_clean_after', '', choices) # I add it here to be able to debug across all iterations

    pp_uoa=ck.get_from_dicts(i, 'post_process_script_uoa','', choices)
    pp_name=ck.get_from_dicts(i, 'post_process_subscript','', choices)
    pp_params=ck.get_from_dicts(i, 'post_process_params', '', choices)

    flags=ck.get_from_dicts(i, 'flags', '', choices)
    lflags=ck.get_from_dicts(i, 'lflags', '', choices)

    no_compile=ck.get_from_dicts(i, 'no_compile', '', choices)
    compile_only_once=ck.get_from_dicts(i, 'compile_only_once', '', choices)
    no_run=ck.get_from_dicts(i, 'no_run', '', choices)
    no_state_check=ck.get_from_dicts(i, 'no_state_check', '', choices)

    env=ck.get_from_dicts(i,'env',{},choices)
    eenv=ck.get_from_dicts(i, 'extra_env','',choices)
    ercmd=ck.get_from_dicts(i, 'extra_run_cmd','',choices)
    rcsub=ck.get_from_dicts(i, 'run_cmd_substitutes',{},choices)

    if i.get('do_not_reuse_repeat','')=='yes' and srn==0:
       repeat=''
    else: 
       repeat=ck.get_from_dicts(i,'repeat','',choices)
       if repeat=='': repeat=state.get('repeat','')

    rsc=ck.get_from_dicts(i, 'skip_calibration','', choices)
    rct=ck.get_from_dicts(i, 'calibration_time','',choices)
    rcm=ck.get_from_dicts(i, 'calibration_max','',choices)

    aff=ck.get_from_dicts(i, 'affinity', '', choices)

    cons=ck.get_from_dicts(i, 'console','',choices)

    tsd=ck.get_from_dicts(i, 'the_same_dataset', '', choices)

    odp=ck.get_from_dicts(i, 'opencl_dvdt_profiler','',choices)

    xcto=ck.get_from_dicts(i, 'compile_timeout','',choices)
    xrto=ck.get_from_dicts(i, 'run_timeout','',choices)

    ###############################################################################################################
    # PIPELINE SECTION: Host and target platform selection
    if o=='con':
       ck.out(sep)
       ck.out('Obtaining platform parameters and checking other obligatory choices for the pipeline ...')
       ck.out('')

    hos=ck.get_from_dicts(i, 'host_os', '', choices)
    tos=ck.get_from_dicts(i, 'target_os', '', choices)
    tbits=ck.get_from_dicts(i, 'target_os_bits', '', choices)
    tdid=ck.get_from_dicts(i, 'device_id', '', choices)

    # Useful when replaying experiments, to retarget them to a local platform
    if i.get('local_platform','')=='yes':
       hos=''
       tos=''
       tbits=''
       tdid=''

    # Get some info about platforms
    ox=oo
    if sdi=='yes' and sic=='yes': ox=''
    ii={'action':'detect',
        'module_uoa':cfg['module_deps']['platform.os'],
        'host_os':hos,
        'target_os':tos,
        'device_id':tdid,
        'skip_device_init':sdi,
        'skip_info_collection':sic,
        'out':ox}
    if si=='yes': ii['return_multi_devices']='yes'
    r=ck.access(ii)
    if r['return']>0: 
       if r['return']==32:
          choices_desc['##device_id']={'type':'text',
                                       'has_choice':'yes',
                                       'choices':r['devices'],
                                       'tags':['setup'],
                                       'sort':1000}
          return finalize_pipeline(i)
       return r

    sdi='yes'
    i['skip_device_init']=sdi

    hos=r['host_os_uoa']
    hosd=r['host_os_dict']

    choices['host_os']=hos

    tos=r['os_uoa']
    tosd=r['os_dict']
    tbits=tosd.get('bits','')

    hosz=hosd.get('base_uoa','')
    if hosz=='': hosz=hos
    tosz=tosd.get('base_uoa','')
    if tosz=='': tosz=tos

    remote=tosd.get('remote','')

    tdid=r['device_id']
    if tdid!='': choices['device_id']=tdid

    choices['target_os']=tos
    choices['target_os_bits']=tbits

    choices['device_id']=r['device_id']

    if hos=='':
       return {'return':1, 'error':'host_os is not defined'}

    if tos=='':
       return {'return':1, 'error':'target_os is not defined'}

    # Get various OS vars
    rx=ck.get_os_ck({})
    if rx['return']>0: return rx
    hplat=rx['platform']

    bbp=hosd.get('batch_bash_prefix','')
    rem=hosd.get('rem','')
    eset=hosd.get('env_set','')
    etset=tosd.get('env_set','')
    svarb=hosd.get('env_var_start','')
    svarb1=hosd.get('env_var_extra1','')
    svare=hosd.get('env_var_stop','')
    svare1=hosd.get('env_var_extra2','')
    scall=hosd.get('env_call','')
    sdirs=hosd.get('dir_sep','')
    sdirsx=tosd.get('remote_dir_sep','')
    if sdirsx=='': sdirsx=sdirs
    stdirs=tosd.get('dir_sep','')
    sext=hosd.get('script_ext','')
    sexe=hosd.get('set_executable','')
    se=tosd.get('file_extensions',{}).get('exe','')
    sbp=hosd.get('bin_prefix','')
    stbp=tosd.get('bin_prefix','')
    sqie=hosd.get('quit_if_error','')
    evs=hosd.get('env_var_separator','')
    envsep=hosd.get('env_separator','')
    envtsep=tosd.get('env_separator','')
    eifs=hosd.get('env_quotes_if_space','')
    eifsc=hosd.get('env_quotes_if_space_in_call','')
    eifsx=tosd.get('remote_env_quotes_if_space','')
    if eifsx=='': eifsx=eifsc
    wb=tosd.get('windows_base','')
    stro=tosd.get('redirect_stdout','')
    stre=tosd.get('redirect_stderr','')
    ubtr=hosd.get('use_bash_to_run','')
    no=tosd.get('no_output','')

    rof=[] # run output files ...
    eppc='' # extra post process CMD

    # check sudo
    sudo_init=tosd.get('sudo_init','')
    if sudo_init=='': sudo_init=svarb+svarb1+'CK_SUDO_INIT'+svare1+svare
    sudo_pre=tosd.get('sudo_pre','')
    if sudo_pre=='': sudo_pre=svarb+svarb1+'CK_SUDO_PRE'+svare1+svare
#    sudo_post=tosd.get('sudo_post','')
#    if sudo_post=='': 
    sudo_post=svarb+svarb1+'CK_SUDO_POST'+svare1+svare

    isd=ck.get_from_dicts(i, 'sudo', '', choices)
    if isd=='': isd=tosd.get('force_sudo','')

    # Check compile type
    ctype=ck.get_from_dicts(i, 'compile_type', '', choices)
    if i.get('static','')=='yes': ctype='static'
    if i.get('dynamic','')=='yes': ctype='dynamic'

    # On default Android-32, use static by default 
    # (old platforms has problems with dynamic)
    if ctype=='':
       if tosd.get('default_compile_type','')!='':
          ctype=tosd['default_compile_type']
       else:
          ctype='dynamic'
    choices['compile_type']=ctype

    if o=='con':
       ck.out(sep)
       ck.out('  Selected host platform: '+hos)
       ck.out('  Selected target platform: '+tos)
       if tdid!='':
          ck.out('  Selected target device ID: '+tdid)

    ###############################################################################################################
    # PIPELINE SECTION: PROGRAM AND DIRECTORY SELECTION 
    #                   (either as CID or CK descrpition from current directory or return that should be selected)

    # First, if duoa is not defined, try to get from current directory
    if len(meta)==0:
       if duoa=='':
          # First, try to detect CID in current directory
          r=ck.cid({})
          if r['return']==0:
             xruoa=r.get('repo_uoa','')
             xmuoa=r.get('module_uoa','')
             xduoa=r.get('data_uoa','')

             rx=ck.access({'action':'load',
                           'module_uoa':xmuoa,
                           'data_uoa':xduoa,
                           'repo_uoa':xruoa})
             if rx['return']>0: return rx
             xmeta=rx['dict']
             xdesc=rx.get('disc',{})

             if xmeta.get('program','')=='yes':
                duoa=xduoa
                muoa=xmuoa
                ruoa=xruoa
                meta=xmeta
                desc=xdesc

          if duoa=='':
             # Attempt to load configuration from the current directory
             pc=os.path.join(state['cur_dir'], ck.cfg['subdir_ck_ext'], ck.cfg['file_meta'])
             if os.path.isfile(pc):
                r=ck.load_json_file({'json_file':pc})
                if r['return']==0:
                   xmeta=r['dict']
                   if xmeta.get('program','')=='yes':
                      meta=xmeta

             px=os.path.join(state['cur_dir'], ck.cfg['subdir_ck_ext'], ck.cfg['file_desc'])
             if os.path.isfile(px):
                r=ck.load_json_file({'json_file':px})
                if r['return']==0:
                   xdesc=r['dict']

    # Second, if duoa is not detected or defined, prepare selection 
    duid=''
    if len(meta)==0:
       if duoa=='': duoa='*'

       r=ck.search({'repo_uoa':ruoa, 'module_uoa':muoa, 'data_uoa':duoa, 'add_info':'yes', 'tags':ptags})
       if r['return']>0: return r

       lst=r['lst']
       if len(lst)==0:
          duoa=''
       elif len(lst)==1:
          duid=lst[0]['data_uid']
          duoa=lst[0]['data_uoa']
       else:
          # SELECTOR *************************************
          choices_desc['##program_uoa']={'type':'uoa',
                                         'has_choice':'yes',
                                         'choices':lst,
                                         'tags':['setup'],
                                         'sort':1000}

          if o=='con' and si!='yes':
             ck.out('************ Selecting program/benchmark/kernel ...')
             ck.out('')
             r=ck.select_uoa({'choices':lst})
             if r['return']>0: return r
             duoa=r['choice']
             ck.out('')
          else:
             return finalize_pipeline(i)

    if len(meta)==0 and duoa=='':
       return {'return':0, 'error':'no programs found for this pipeline'}

    if pdir=='' and duoa!='':
       rx=ck.access({'action':'load',
                     'module_uoa':muoa,
                     'data_uoa':duoa,
                     'repo_uoa':ruoa})
       if rx['return']>0: return rx
       if len(meta)==0: 
          meta=rx['dict']
       if len(desc)==0:
          desc=rx.get('desc',{})

       pdir=rx['path']
       duid=rx['data_uid']
       duoa=rx['data_uoa']

       # Check if base_uoa suggests to use another program path
       buoa=meta.get('base_uoa','')
       if buoa!='':
          rx=ck.access({'action':'find',
                        'module_uoa':muoa,
                        'data_uoa':buoa})
          if rx['return']>0:
             return {'return':1, 'error':'problem finding base entry '+buoa+' ('+rx['error']+')'}

          pdir=rx['path']

    if pdir=='': pdir=state['cur_dir']

    if duid=='': 
        # Write program meta and desc only if no program UID, otherwise can restore from program entry
       i['program_meta']=meta
       i['program_desc']=desc

    if duid=='' and meta.get('backup_data_uid','')!='': duid=meta['backup_data_uid']

    if duoa!='': choices['data_uoa']=duoa
    if muoa!='': choices['module_uoa']=muoa
    # we are not recording repo_uoa for reproducibility (can be different across users) ...   

    if o=='con':
       ck.out('  Selected program: '+duoa+' ('+duid+')')

    ###############################################################################################################
    # PIPELINE SECTION: Command line selection 

    run_cmds=meta.get('run_cmds',{})
    if len(run_cmds)==0:
       return {'return':1, 'error':'no CMD for run'}

    krun_cmds=sorted(list(run_cmds.keys()))
    zrt={}
    if kcmd=='':
       if len(krun_cmds)>1:
          xchoices=[]
          dchoices=[]
          for z in sorted(krun_cmds):
              xchoices.append(z)

              zrt=run_cmds[z].get('run_time',{})
              zcmd=zrt.get('run_cmd_main','')
              dchoices.append(zcmd)

          # SELECTOR *************************************
          choices_desc['##cmd_key']={'type':'text',
                                     'has_choice':'yes',
                                     'choices':xchoices,
                                     'tags':['setup'],
                                     'sort':1100}

          if o=='con' and si!='yes':
             ck.out('************ Selecting command line ...')
             ck.out('')
             r=ck.access({'action':'select_list',
                          'module_uoa':cfg['module_deps']['choice'],
                          'choices':xchoices,
                          'desc':dchoices})
             if r['return']>0: return r
             kcmd=r['choice']
             ck.out('')
          else:
             return finalize_pipeline(i)

       else:
          kcmd=krun_cmds[0]
    else:
       if kcmd not in krun_cmds:
          return {'return':1, 'error':'CMD key "'+kcmd+'" not found in program description'}

    choices['cmd_key']=kcmd

    if o=='con':
       ck.out('  Selected command line: '+kcmd)

    ###############################################################################################################
    # PIPELINE SECTION: dataset selection 
    vcmd=run_cmds[kcmd]

    dtags=vcmd.get('dataset_tags',[])
    dmuoa=cfg['module_deps']['dataset']
    dduid=''

    xdtags=''
    for q in dtags:
        if xdtags!='': xdtags+=','
        xdtags+=q

    if no_run!='yes' and (dduoa!='' or len(dtags)>0):
       if dduoa=='':
          rx=ck.access({'action':'search',
                        'dataset_repo_uoa':druoa,
                        'module_uoa':dmuoa,
                        'tags':xdtags})
          if rx['return']>0: return rx

          lst=rx['lst']

          xchoices=[]
          for z in lst:
              xchoices.append(z['data_uid'])

          if len(lst)==0:
             duoa=''
          elif len(lst)==1:
             dduid=lst[0]['data_uid']
             dduoa=lst[0]['data_uoa']
          else:
             # SELECTOR *************************************
             choices_desc['##dataset_uoa']={'type':'uoa',
                                            'has_choice':'yes',
                                            'choices':xchoices,
                                            'tags':['setup', 'dataset'],
                                            'sort':1200}

             if o=='con' and si!='yes':
                ck.out('************ Selecting data set ...')
                ck.out('')
                r=ck.select_uoa({'choices':lst})
                if r['return']>0: return r
                dduoa=r['choice']
                ck.out('')
             else:
                return finalize_pipeline(i)

       if dduoa=='':
          return {'return':1, 'error':'no datasets found for this pipeline'}

    ddmeta={}
    if dduoa!='':
       rx=ck.access({'action':'load',
                     'dataset_repo_uoa':druoa,
                     'module_uoa':dmuoa,
                     'data_uoa':dduoa})
       if rx['return']>0: return rx
       ddmeta=rx['dict']
       dduid=rx['data_uid']
       dduoa=rx['data_uoa']

    if dduoa!='': 
       choices['dataset_uoa']=dduoa

       if o=='con':
          ck.out('  Selected data set: '+dduoa+' ('+dduid+')')

    ###############################################################################################################
    # PIPELINE SECTION: dataset file selection (if more than one in one entry)
    ddfiles=ddmeta.get('dataset_files',[])

    choices_desc['##dataset_file']={'type':'text',
                                    'has_choice':'yes',
                                    'choices':ddfiles,
                                    'tags':['setup'],
                                    'sort':1100}

    if ddfile=='':
       if len(ddfiles)==1:
          ddfile=ddfiles[0]
       elif len(ddfiles)>0:
          if o=='con' and si!='yes':
             ck.out('************ Selecting dataset file ...')
             ck.out('')
             r=ck.access({'action':'select_list',
                          'module_uoa':cfg['module_deps']['choice'],
                          'choices':ddfiles,
                          'desc':ddfiles})
             if r['return']>0: return r
             ddfile=r['choice']
             ck.out('')
          else:
             return finalize_pipeline(i)

    choices['dataset_file']=ddfile

    if ddfile!='' and o=='con':
       ck.out('  Selected dataset file: '+ddfile)

    ###############################################################################################################
    # PIPELINE SECTION: resolve compile dependencies 
    if ceuoa!='':
       rx=ck.access({'action':'load',
                     'module_uoa':cfg['module_deps']['env'],
                     'data_uoa':ceuoa})
       if rx['return']>0: return rx
       ceuoa=rx['data_uid']

    if no_compile!='yes':
       if len(cdeps)==0 or ceuoa!='': 
          cdeps=meta.get('compile_deps',{})

          if len(cdeps)>0:
             if o=='con':
                ck.out(sep)

             if ceuoa!='':
                # clean compiler version, otherwise wrong detection of flags
                if 'compiler_version' in features: del(features['compiler_version'])
                x=cdeps.get('compiler',{})
                if len(x)>0:
                   if 'cus' in x: del(x['cus'])
                   if 'deps' in x: del(x['deps'])
                   x['uoa']=ceuoa
                   cdeps['compiler']=x

             ii={'action':'resolve',
                 'module_uoa':cfg['module_deps']['env'],
                 'host_os':hos,
                 'target_os':tos,
                 'device_id':tdid,
                 'deps':cdeps,
                 'add_customize':'yes',
                 'out':oo}

             rx=ck.access(ii)
             if rx['return']>0: return rx

             cdeps=rx['deps'] # Update deps (add UOA)
             i['dependencies']=cdeps

             # Check if multiple compiler choices
             cmpl=cdeps.get('compiler',{}).get('choices',[])
             if len(cmpl)>0 and len(choices_desc.get('##compiler_env_uoa',{}))==0:
                choices_desc['##compiler_env_uoa']={'type':'uoa',
                                                    'has_choice':'yes',
                                                    'choices':cmpl,
                                                    'sort':2000}

       else:
          if o=='con':
             ck.out('  Selected dependencies: ')
             for dp in cdeps:
                 dpx=cdeps[dp]
                 tags=dpx.get('dict',{}).get('tags',[])
                 x=json.dumps(tags, sort_keys=True)
                 y=dpx.get('uoa','')
                 ck.out('      '+dp+' env = '+y+'; tags = '+x)

    ###############################################################################################################
    # PIPELINE SECTION: Detect compiler version
    if no_compile!='yes' and i.get('no_detect_compiler_version','')!='yes' and len(features.get('compiler_version',{}))==0:
       if o=='con':
          ck.out(sep)
          ck.out('Detecting compiler version ...')
          ck.out('')

       if no_compile!='yes':
          ii={'sub_action':'get_compiler_version',
              'host_os':hos,
              'target_os':tos,
              'deviced_id':tdid,
              'path':pdir,
              'meta':meta,
              'deps':cdeps,
              'generate_rnd_tmp_dir':grtd,
              'tmp_dir':tdir,
              'skip_clean_after':sca,
              'compile_type':ctype,
              'flags':flags,
              'lflags':lflags,
              'console':cons,
              'env':env,
              'extra_env':eenv,
              'out':oo}
          r=process_in_dir(ii)
          if r['return']>0: return r

          misc=r['misc']
          tdir=misc.get('tmp_dir','')
          if tdir!='': state['tmp_dir']=tdir

          features['compiler_version']={'list':misc.get('compiler_detected_ver_list',[]),
                                        'str':misc.get('compiler_detected_ver_str',''),
                                        'raw':misc.get('compiler_detected_ver_raw','')}

    ###############################################################################################################
    # PIPELINE SECTION: get compiler description for flag options
    cflags_desc=choices_desc.get('##compiler_flags',{})

    cdu=i.get('compiler_description_uoa','')
    if no_compile!='yes' and cdu=='' and i.get('no_compiler_description','')!='yes':
       cdt=cdeps.get('compiler',{}).get('dict',{}).get('tags',[])

       # Substitute with real compiler version
       creal=features.get('compiler_version',{}).get('list',[])
       if len(creal)>0:
          cdt1=[]
          for q in cdt:
              if not q.startswith('v'): cdt1.append(q)
          qq=''
          for q in creal:
              if qq=='': qq='v'
              else: qq+='.'
              qq+=q
              cdt1.append(qq)

          # Find most close
          ii={'action':'list',
              'module_uoa':cfg['module_deps']['compiler'],
              'add_meta':'yes',
              'tags':'auto'}
          rx=ck.access(ii)
          if rx['return']>0: return rx

          rl=rx['lst']

          xrmax=0 # max tag matches
          xruid=''
          xruoa=''

          for q in rl:
              qdt=q.get('meta',{}).get('tags',[])
              rx=0
              for qi in cdt1:
                  if qi in qdt:
                     rx+=1
              if rx>xrmax:
                 xrmax=rx
                 xruid=q['data_uid']
                 xruoa=q['data_uoa']

          if xrmax==0:
             return {'return':1, 'error':'can\'t find most close compiler description by tags ('+json.dumps(cdt1)+')'}

          cdu=xruoa

          if o=='con':
             ck.out('')
             ck.out('Most close found compiler description: '+xruoa+' ('+xruid+')')

    if cdu!='':
       rx=ck.access({'action':'load',
                     'module_uoa':cfg['module_deps']['compiler'],
                     'data_uoa':cdu})
       if rx['return']>0: return rx
       xruid=rx['data_uid']
       rxd=rx['dict']
       rxdd=rx.get('desc',{})

       if o=='con':
          ck.out('')
          ck.out('Loading compiler description: '+cdu+' ('+xruid+') ...')

       if len(cflags_desc)==0:
          cflags_desc=rxdd.get('all_compiler_flags_desc',{})

          for q in cflags_desc:
              qq=cflags_desc[q]
              q1=q
              if q.startswith('##'):q1=q[2:]
              elif q.startswith('#'):q1=q[1:]
              choices_desc['##compiler_flags#'+q1]=qq

    ###############################################################################################################
    # PIPELINE SECTION: get compiler vars choices (-Dvar=value) - often for datasets such as in polyhedral benchmarks
    bcvd=desc.get('build_compiler_vars_desc',{})
    for q in bcvd:
        qq=bcvd[q]
        q1=q
        if q.startswith('##'):q1=q[2:]
        elif q.startswith('#'):q1=q[1:]
        choices_desc['##compiler_vars#'+q1]=qq

    cv=ck.get_from_dicts(i,'compiler_vars',{},choices)
    rcv=ck.get_from_dicts(i,'remove_compiler_vars',[],choices)
    eefc=ck.get_from_dicts(i,'extra_env_for_compilation',{},choices)

    ###############################################################################################################
    # PIPELINE SECTION: get run vars (preset environment)
    rv=desc.get('run_vars_desc',{})
    for q in rv:
        qq=rv[q]
        q1=q
        if q.startswith('##'):q1=q[2:]
        elif q.startswith('#'):q1=q[1:]
        choices_desc['##env#'+q1]=qq

    env=ck.get_from_dicts(i,'env',{},choices)

    ###############################################################################################################
    # Pipeline ready for compile/run
    i['ready']='yes'
    if pr=='yes':
       return finalize_pipeline(i)

    ###############################################################################################################

    # Restore compiler flag selection with order for optimization reordering (!)
    # Simplified - needs to be improved for more complex cases (dict of dict)
    compiler_flags=ck.get_from_dicts(i, 'compiler_flags', {}, choices)

    # Check if use best base flag
    bbf=ck.get_from_dicts(i, 'best_base_flag', '', None)
    if bbf=='':
       bbf=ck.get_from_dicts(i, 'speed', '', None)
    if bbf=='yes':
       qx=choices_desc.get('##compiler_flags#base_opt',{}).get('choice',[])
       if len(qx)>0:
          compiler_flags['base_opt']=qx[0]
          if '##compiler_flags#base_opt' not in choices_order:
             choices_order.insert(0,'##compiler_flags#base_opt')

    for q in compiler_flags:
        if '##compiler_flags#'+q not in choices_order:
           choices_order.append('##compiler_flags#'+q)

    if len(compiler_flags)>0:
       # Check if compiler flags are not in order (to set some order for reproducibility)
       # At the same time clean up choices_order with non-used flags
       compiler_flags_used={}
       for q in choices_order:
           if q.startswith('##compiler_flags#'):
              qk=q[17:]
              if qk in compiler_flags:
                 qq=compiler_flags[qk]
                 if qq!=None and qq!='':
                    compiler_flags_used[qk]=qq
                    if flags!='': flags+=' '
                    flags+=str(qq)
       compiler_flags=compiler_flags_used

    # to be able to properly record info
    choices['compiler_flags']=compiler_flags

    ###############################################################################################################
    # PIPELINE SECTION: use gprof for profiling
    gprof_tmp=''
    if gprof=='yes':
       if o=='con':
          ck.out(sep)
          ck.out('Adding gprof compilation flag ...')
          ck.out('')

       flags=svarb+svarb1+'CK_COMPILER_FLAG_GPROF'+svare1+svare+' '+flags
       lflags=svarb+svarb1+'CK_COMPILER_FLAG_GPROF'+svare1+svare+' '+lflags

       if cfg['gprof_file'] not in rof: rof.append(cfg['gprof_file'])

       rx=ck.gen_tmp_file({'prefix':'tmp-', 'remove_dir':'yes'})
       if rx['return']>0: return rx
       gprof_tmp=rx['file_name']

       eppc+='\n'+svarb+svarb1+'CK_PROFILER'+svare1+svare+' $#BIN_FILE#$ > '+gprof_tmp

    ###############################################################################################################
    # PIPELINE SECTION: set CPU frequency
    if scpuf!='':
       if o=='con':
          ck.out(sep)
          ck.out('Setting CPU frequency to '+str(scpuf)+' (if supported) ...')
          ck.out('')

       env['CK_CPU_FREQUENCY']=scpuf

       ii={'action':'set_freq',
           'module_uoa':cfg['module_deps']['platform.cpu'],
           'value':scpuf,
           'host_os':hos,
           'target_os':tos,
           'device_id':tdid,
           'skip_print_os':'yes',
           'skip_device_init':sdi,
           'skip_info_collection':sic,
           'out':oo}
       r=ck.access(ii)
       if r['return']>0: return r

    ###############################################################################################################
    # PIPELINE SECTION: set GPU frequency
    if sgpuf!='':
       if o=='con':
          ck.out(sep)
          ck.out('Setting GPU frequency to '+str(sgpuf)+' (if supported) ...')
          ck.out('')

       env['CK_GPU_FREQUENCY']=sgpuf

       ii={'action':'set_freq',
           'module_uoa':cfg['module_deps']['platform.accelerator'],
           'value':sgpuf,
           'host_os':hos,
           'target_os':tos,
           'device_id':tdid,
           'skip_print_os':'yes',
           'skip_device_init':sdi,
           'skip_info_collection':sic,
           'out':oo}
       r=ck.access(ii)
       if r['return']>0: return r

    ###############################################################################################################
    # PIPELINE SECTION: get target platform features
    npf=i.get('no_platform_features','')
    if i.get('platform_features','')!='yes' and npf!='yes':
       if o=='con':
          ck.out(sep)
          ck.out('Detecting all target platform features ...')
          ck.out('')

       # Get some info about platforms
       ii={'action':'detect',
           'module_uoa':cfg['module_deps']['platform'],
           'host_os':hos,
           'target_os':tos,
           'device_id':tdid,
           'skip_print_os':'yes',
           'skip_device_init':sdi,
           'skip_info_collection':sic,
           'out':oo}
       r=ck.access(ii)
       if r['return']>0: return r

       features['platform']=r.get('features',{})
       i['platform_features']='yes'
       i['skip_info_collection']='yes'

    ###############################################################################################################
    # PIPELINE SECTION: get dataset features
    npf=i.get('no_dataset_features','')
    if npf!='yes' and dduid!='':
       if o=='con':
          ck.out(sep)
          ck.out('Checking dataset features for '+dduoa+' ('+dduid+') ...')
          ck.out('')

       dsf=features.get('dataset',{})
       dsf1={}

       # Get some info about platforms (the same id as program UID)
       ii={'action':'load',
           'repo_uoa':druoa,
           'module_uoa':cfg['module_deps']['dataset.features'],
           'data_uoa':dduid}
       r=ck.access(ii)
       if r['return']>0: 
          if r['return']==16:
             # Try to extract
             if o=='con':
                ck.out(sep)
                ck.out('Trying to extract dataset features ...')
                ck.out('')

             ii['tags']=xdtags
             ii['action']='extract'
             ii['out']=oo
             r=ck.access(ii)
             if r['return']==0:
                dsf1=r['dict'].get('features',{})

          # Ignore errors
       else:
          dsf1=r['dict'].get('features',{})

       if len(dsf1)>0 and o=='con':
          ck.out('Features found:')
          ck.out('  '+json.dumps(dsf1))

       dsf.update(dsf1)
       features['dataset']=dsf

    ###############################################################################################################
    # PIPELINE SECTION: Check that system state didn't change (frequency)
    if no_state_check!='yes':
       if o=='con': ck.out(sep)

       ii={'action':'detect',
           'module_uoa':cfg['module_deps']['platform.cpu'],
           'host_os':hos,
           'target_os':tos,
           'device_id':tdid,
           'skip_print_os_info':'yes',
           'skip_device_init':sdi,
           'skip_info_collection':sic,
           'out':oo} # skip here since it's second time ...
       r=ck.access(ii)
       if r['return']==0:
          xft=r.get('features',{})
          xft1=xft.get('cpu',{})
          xft2=xft.get('cpu_misc',{})
          features['platform.cpu']=xft

          freq1=xft1.get('current_freq',{})
          chars['current_freq']=freq1

          sft=state.get('features.platform.cpu',{})
          if len(sft)==0 or (srn==0 and ati==0):
             state['features.platform.cpu']=xft1
          else:
             freq2=sft.get('current_freq',{})

             if o=='con':
                ck.out('')
                ck.out('Checking CPU frequency:')
                ck.out('')
                ck.out('  Now:    '+json.dumps(freq1, sort_keys=True))
                ck.out('         vs')
                ck.out('  Before: '+json.dumps(freq2, sort_keys=True))
                ck.out('')

             equal=True
             for icpu in freq2:
                 if icpu not in freq1:
                    equal=False
                    break
                 ff1=float(freq1[icpu])
                 ff2=float(freq2[icpu])
                 if ff2!=0:
                    diff=ff1/ff2
                 else:
                    equal=False
                    break
                 if diff<0.98 or diff>1.02:
                    equal=False
                    break

             if not equal:
                if o=='con':
                   ck.out('CPU frequency changed over iterations:')
                   ck.out('')
                i['fail_reason']='frequency changed during experiments'
                i['fail']='yes'
             else:
                ck.out('CPU frequency stays the same ...')
                ck.out('')

    ###############################################################################################################
    # PIPELINE SECTION: Compile program
    cs='yes'
    if i.get('fail','')!='yes' and no_compile!='yes' and \
       (compile_only_once!='yes' or ai==0) and \
       (srn==0 or (srn>0 and i.get('repeat_compilation','')=='yes')):
       if o=='con':
          ck.out(sep)
          ck.out('Compile program ...')
          ck.out('')

       cl=i.get('clean','')
       if cl=='' and i.get('no_clean','')!='yes' and srn==0: cl='yes'

       if o=='con' and cl=='yes':
          ck.out('Cleaning working directory ...')
          ck.out('')

       if meta.get('no_compile','')!='yes' and no_compile!='yes':
          ii={'sub_action':'compile',
              'host_os':hos,
              'target_os':tos,
              'deviced_id':tdid,
              'path':pdir,
              'meta':meta,
              'deps':cdeps,
              'generate_rnd_tmp_dir':grtd,
              'tmp_dir':tdir,
              'clean':cl,
              'skip_clean_after':sca,
              'compile_type':ctype,
              'flags':flags,
              'lflags':lflags,
              'statistical_repetition':srn,
              'autotuning_iteration':ati,
              'console':cons,
              'env':env,
              'extra_env':eenv,
              'compiler_vars':cv,
              'remove_compiler_vars':rcv,
              'extra_env_for_compilation':eefc,
              'compile_timeout':xcto,
              'out':oo}
          r=process_in_dir(ii)
          if r['return']>0: return r

          misc=r['misc']
          tdir=misc.get('tmp_dir','')
          if tdir!='': state['tmp_dir']=tdir

          cch=r['characteristics']
          cch['joined_compiler_flags']=flags # Add joint compilation flags as string from previous sections
          chars['compile']=cch

          xct=cch.get('compilation_time',-1)
          xos=cch.get('obj_size',-1)

          cs=misc.get('compilation_success','')
          if cs=='no': 
             x='compilation failed'
             if misc.get('fail_reason','')!='': x+=' - '+misc['fail_reason']
             i['fail_reason']=x
             i['fail']='yes'

    ###############################################################################################################
    # PIPELINE SECTION: Check if dataset is the same
    sdc='no'
    if tsd=='yes' and (ati!=0 or srn!=0):
       sdc='yes'


    ###############################################################################################################
    # PIPELINE SECTION: perf
    perf_tmp=''
    if perf=='yes':
       if o=='con':
          ck.out(sep)
          ck.out('Preparing perf ...')

       rx=ck.gen_tmp_file({'prefix':'tmp-', 'remove_dir':'yes'})
       if rx['return']>0: return rx
       perf_tmp=rx['file_name']

       prcmd='perf stat -x, -o '+perf_tmp

       if perf_tmp not in rof: rof.append(perf_tmp)

    ###############################################################################################################
    # PIPELINE SECTION: Intel vTune 
    vtune_tmp=''
    vtune_tmp1=''
    if vtune=='yes':
       if o=='con':
          ck.out(sep)
          ck.out('Preparing vtune ...')

       if 'vtune_profiler' not in cdeps:
          cdeps['vtune_profiler']={'local':'yes', 'tags':'perf,intel,vtune'}

       if hplat=='win':
          eenv='\nrd /S /Q r000\n'+eenv
       else:
          eenv='\nrm -rf r000\n'+eenv

       prcmd='amplxe-runss -r r000 -event-based-counts --'

       rx=ck.gen_tmp_file({'prefix':'tmp-', 'remove_dir':'yes'})
       if rx['return']>0: return rx
       vtune_tmp=rx['file_name']
       vtune_tmp1=vtune_tmp+'.csv'

       if vtune_tmp1 not in rof: rof.append(vtune_tmp1)

       eppc+='\namplxe-cl -report hw-events -r r000 -report-output='+vtune_tmp+' -format csv -csv-delimiter=comma -filter module=$#ONLY_BIN_FILE#$'

    ###############################################################################################################
    # PIPELINE SECTION: Check OpenCL DVDT profiler
    if odp=='yes':
       if hplat=='win':
          return {'return':1, 'error':'OpenCL DVDT profiler currently does not support Windows'}

       if 'opencl_dvdt_profiler' not in cdeps:
          cdeps['opencl_dvdt_profiler']={'local':'yes', 'tags':'plugin,opencl,dvdt,profiler'}

       eenv='export LD_PRELOAD="${CK_ENV_PLUGIN_OPENCL_DVDT_PROFILER_DYNAMIC_NAME_FULL}"; '+eenv

       fodp='tmp-opencl-dvdt-output.json'
       if os.path.isfile(fodp): os.remove(fodp)

    ###############################################################################################################
    # PIPELINE SECTION: Run program
    xdeps={}
    if i.get('fail','')!='yes' and cs!='no' and no_run!='yes':
       if o=='con':
          ck.out(sep)
          ck.out('Running program ...')

       # Check run cmd keys subst
       for k in choices:
           if k.startswith('run_cmd_key_'):
              rcsub[k]=choices[k]

       ii={'sub_action':'run',
           'host_os':hos,
           'target_os':tos,
           'deviced_id':tdid,
           'path':pdir,
           'console':cons,
           'meta':meta,
           'deps':cdeps,
           'cmd_key':kcmd,
           'dataset_uoa':dduoa,
           'dataset_file':ddfile,
           'generate_rnd_tmp_dir':grtd,
           'tmp_dir':tdir,
           'skip_clean_after':sca,
           'compile_type':ctype,
           'sudo':isd,
           'energy':sme,
           'affinity':aff,
           'flags':flags,
           'lflags':lflags,
           'repeat':repeat,
           'pre_run_cmd':prcmd,
           'run_output_files':rof,
           'skip_calibration':rsc,
           'calibration_time':rct,
           'calibration_max':rcm,
           'post_process_script_uoa':pp_uoa,
           'post_process_subscript':pp_name,
           'post_process_params':pp_params,
           'statistical_repetition':srn,
           'autotuning_iteration':ati,
           'skip_dataset_copy':sdc,
           'env':env,
           'extra_env':eenv,
           'extra_run_cmd':ercmd,
           'extra_post_process_cmd':eppc,
           'run_cmd_substitutes':rcsub,
           'compiler_vars':cv,
           'remove_compiler_vars':rcv,
           'extra_env_for_compilation':eefc,
           'run_timeout':xrto,
           'out':oo}
       r=process_in_dir(ii)
       if r['return']>0: return r

       misc=r['misc']
       tdir=misc.get('tmp_dir','')
       if tdir!='': state['tmp_dir']=tdir

       rch=r['characteristics']
       chars['run']=rch

       xdeps=r.get('deps',{})

       csuc=misc.get('calibration_success',True)
       rs=misc.get('run_success','')
       rsf=misc.get('fail_reason','')

       repeat=rch.get('repeat','')
       if repeat!='': 
          state['repeat']=repeat
          choices['repeat']=repeat

       if rs=='no' or not csuc:
          x='execution failed'
          if rsf!='': x+=' - '+rsf
          i['fail_reason']=x
          i['fail']='yes'

    ###############################################################################################################
    # PIPELINE SECTION: finish vtune
    if vtune=='yes':
       if o=='con':
          ck.out(sep)
          ck.out('Processing Intel vTune output ...')
          ck.out('')

       if os.path.isfile(vtune_tmp1):
          import csv

          clk='Hardware Event Count:CPU_CLK_UNHALTED.THREAD:Self'
          inst='Hardware Event Count:INST_RETIRED.ANY:Self'

          f=open(vtune_tmp1, 'rb')
          c=csv.reader(f, delimiter=',')

          hc=[]
          val={}

          first=True
          for q in c:
              if first:
                 first=False
                 if len(q)>1:
                    for k in range(2,len(q)):
                        hc.append(q[k])
              else:
                 func=q[0]
                 module=q[1]

                 if len(q)>1:
                    for k in range(2,len(q)):
                        val[hc[k-2]]=q[k]

                 break

          f.close()

          if sca!='yes':
             os.remove(vtune_tmp1)

          if len(val)>0:
             if clk in val and inst in val:
                cpi=0
                try:
                   cpi=float(val[clk])/float(val[inst])
                except ValueError:
                   pass
                if cpi!=0:
                   chars['run']['global_cpi']=cpi
                   chars['run']['global_clock']=float(val[clk])
                   chars['run']['global_instructions_retired']=float(val[inst])

    ###############################################################################################################
    # PIPELINE SECTION: finish perf
    if perf=='yes':
       if o=='con':
          ck.out(sep)
          ck.out('Processing perf output ...')
          ck.out('')

       if os.path.isfile(perf_tmp):
          ii={'text_file':perf_tmp, 
              'split_to_list':'yes', 
              'encoding':sys.stdin.encoding}
#          if sca!='yes': 
#             ii['delete_after_read']='yes'

          rx=ck.load_text_file(ii)
          if rx['return']>0: return rx
          glst=rx['lst']

          clk='cycles'
          inst='instructions'
          val={}
          found=False
          for lx in glst:
             l=lx.strip()
             if found:
                x=l.find(',')
                if x>0:
                   v=l[0:x]

                   try:
                      v=float(v)
                   except ValueError:
                      pass

                   y=l.rfind(',')
                   if y>x:
                      key=l[y+1:]
                      val[key]=v
             elif l.find(',task-clock')>0:
                found=True

          if sca!='yes':
             os.remove(perf_tmp)

          if len(val)>0:
             if clk in val and inst in val:
                cpi=0
                try:
                   cpi=val[clk]/val[inst]
                except ValueError:
                   pass
                if cpi!=0:
                   chars['run']['global_cpi']=cpi
                   chars['run']['global_clock']=val[clk]
                   chars['run']['global_instructions_retired']=val[inst]
                   chars['run']['perf']=val

    ###############################################################################################################
    # PIPELINE SECTION: finish gprof
    if gprof=='yes':
       if o=='con':
          ck.out(sep)
          ck.out('Processing gprof output ...')
          ck.out('')

       if os.path.isfile(cfg['gprof_file']):
          ii={'text_file':gprof_tmp, 
              'split_to_list':'yes', 
              'encoding':sys.stdin.encoding}
          if sca!='yes': 
             ii['delete_after_read']='yes'

          rx=ck.load_text_file(ii)
          if rx['return']>0: return rx
          glst=rx['lst']

          process=False
          cgprof={}
          for g in glst:
              if g.startswith(' time'):
                 process=True
                 continue

              if process:
                 if g=='':
                    break

                 gg=g.replace('  ','').split(' ')
                 igg=len(gg)
                 if igg>0:
                    cgprof[gg[igg-1]]=gg

          chars['run']['gprof']=cgprof
          chars['run']['gprof_list']=glst

    ###############################################################################################################
    # PIPELINE SECTION: Check OpenCL DVDT profiler
    if odp=='yes':
       y=xdeps.get('opencl_dvdt_profiler',{}).get('bat','').rstrip()+' '+envsep

       y+=' \\'+svarb+svarb1+'CK_ENV_PLUGIN_OPENCL_DVDT_PROFILER_CONVERT_TO_CK'+svare1+svare+' '+vcmd.get('run_time',{}).get('run_cmd_out1','')+' '+fodp

       if ubtr!='': y=ubtr.replace('$#cmd#$',y)

       if o=='con':
          ck.out('')
          ck.out('  (post processing OpenCL DVDT profiler ...)')
          ck.out('')
          ck.out(y)
          ck.out('')

       rx=os.system(y)

       rx=ck.load_json_file({'json_file':fodp})
       if rx['return']>0: return rx
       chars['run']['opencl_dvdt_profiler']=rx['dict']

    ###############################################################################################################
    # Deinit remote device, if needed
    ndi=i.get('no_deinit_remote_device','')
    if remote=='yes' and ndi!='yes':
       r=ck.access({'action':'init_device',
                    'module_uoa':cfg['module_deps']['platform'],
                    'os_dict':tosd,
                    'device_id':tdid,
                    'key':'remote_deinit'})
       if r['return']>0: return r

    ###############################################################################################################
    # PIPELINE SECTION: finalize PIPELINE
    i['out']=o
    return finalize_pipeline(i)

##############################################################################
# finalize pipeline
def finalize_pipeline(i):
    """
    Input:  {
              Input from pipeline that will be passed as output
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    import os

    o=i.get('out','')

    state=i.get('state',{})
    pr=i.get('prepare','')

    fail=i.get('fail','')
    fail_reason=i.get('fail_reason','')

    stfx=i.get('save_to_file','')
    stf=stfx
    cd=state.get('cur_dir','')
    if not os.path.isabs(stf):
       stf=os.path.join(cd, stf)

    # Cleaning input/output
    for q in cfg['clean_vars_in_output']:
        if q in i:
           del(i[q])

    if stfx!='':
       if o=='con':
          ck.out(sep)
          ck.out('Writing state to file '+stf+' ...')

       rx=ck.save_json_to_file({'json_file':stf,
                                'dict':i,
                                'sort_keys':'yes'})
       if rx['return']>0: return rx

    if o=='con':
       ck.out(sep)
       if i.get('ready','')=='yes':
          if pr=='yes':
             ck.out('Pipeline is ready!')
          else:
             if fail=='yes':
                x=''
                if fail_reason!='': x=' ('+fail_reason+')'
                ck.out('Pipeline failed'+x+'!')
             else:
                ck.out('Pipeline executed successfully!')
       else:
          ck.out('Pipeline is NOT YET READY - multiple choices exists!')

    i['return']=0

    return i

##############################################################################
# substitute some CK reserved keys
#   $#ck_take_from{CID or UID}#$ (if module_uoa omitted, use current one)
#   $#ck_host_os_sep#$

def substitute_some_ck_keys(i):
    """
    Input:  {
              string
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              string       - 
              path         - if substitute ck_take_from_{
            }

    """

    import os

    s=i['string']
    p=''

    b1=s.find('$#ck_take_from_{')
    if b1>=0:
       b2=s.find('}#$', b1)
       if b2<0:
          return {'return':1, 'error':'wrong format of the $#ck_take_from{}#$ ('+s+')'}
       bb=s[b1+16:b2]

       rx=ck.parse_cid({'cid':bb})
       if rx['return']==0: 
          ruoa=rx.get('repo_uoa','')
          muoa=rx.get('module_uoa','')
          duoa=rx.get('data_uoa','')
       else:
          ruoa=''
          muoa=work['self_module_uid']
          duoa=bb

       rb=ck.access({'action':'load',
                     'module_uoa':muoa,
                     'data_uoa':duoa,
                     'repo_uoa':ruoa})
       if rb['return']>0: return rb

       p=rb['path']

       s=s[:b1]+p+os.path.sep+s[b2+3:]

    s=s.replace('$#ck_host_os_sep#$', os.path.sep)

    return {'return':0, 'string':s, 'path':p}

##############################################################################
# copy program

def cp(i):
    """
    Input:  {
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    i['common_func']='yes'
    r=ck.access(i)

    ruid=r['repo_uid']
    muid=r['module_uid']
    duid=r['data_uid']
    d=r['dict']

    d['backup_data_uid']=duid

    ii={'action':'update',
        'module_uoa':muid,
        'repo_uoa':ruid,
        'data_uoa':duid,
        'dict':d,
        'ignore_update':'yes',
        'sort_keys':'yes'}

    return ck.access(ii)

##############################################################################
# crowdtune program (redirecting to crowdsource program.optimization from ck-crowdtuning)

def crowdtune(i):
    """
    Input:  {
               See 'crowdsource program.optimization'
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    o=i.get('out','')

    m=cfg['module_program_optimization']

    # Check if module exists
    r=ck.access({'action':'find', 'module_uoa':'module', 'data_uoa':m})
    if r['return']>0:
       if o=='con':
          ck.out('Module "program.optimization" doesn\'t exist!')
          ck.out('')
          ck.out('Please, try to install shared repository "ck-crowdtuning"')
          ck.out('  $ ck pull repo:ck-crowdtuning')
          ck.out('')

       return r

    # Redirecting to crowdsource program.optimization
    i['action']='crowdsource'
    i['module_uoa']=m

    return ck.access(i)
