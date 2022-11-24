R0000GA.xml: base fit using the GA algorithm, it requires the following ModelOptions to be set to false:
<ModelOptions>
    <option name="INNATE_MAX_DENS" value="false"/>
    <option name="INDIRECT_MORTALITY_FIX" value="false"/>
</ModelOptions>

2022.11.01: new fit using the gaussian process regression. It works with all default ModelOptions.