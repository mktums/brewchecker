require 'formula'
require 'patch'
require 'json'

output = {}

Formula.each do |f|
  s = f.stable
  r = s.resources
  re = s.instance_variable_get('@resource')

  # Stable
  output["#{f.name}"] = {
    :main => {
      :url => re.url, :specs => re.specs, :mirrors => re.mirrors, :using => re.using, :strategy => re.download_strategy
    }
  }

  # Patches
  output["#{f.name}"]["patches"] = s.patches.select {|x| x.is_a? ExternalPatch}.collect {|x| {
    :url => x.resource.url,
    :specs => x.resource.specs,
    :mirrors => x.resource.mirrors,
    :using => x.resource.using,
    :strategy => x.resource.download_strategy
  }}

  # Resources
  output["#{f.name}"]["resources"] = Hash[r.collect {|_, x| [x.name, {
    :url => x.url,
    :specs => x.specs,
    :mirrors => x.mirrors,
    :using => x.using,
    :strategy => x.download_strategy
  }]}]
end

puts output.to_json

exit
